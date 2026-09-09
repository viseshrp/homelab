"""Small transfer contract and the rclone implementation. No shell execution."""

import asyncio
import csv
import io
import json
import os
import shlex
import shutil
import signal
import sys
from collections import deque
from pathlib import Path
from typing import Protocol

from .config import Config, Host, Job
from .events import Event, EventSink


class TransferError(RuntimeError):
    pass


class Backend(Protocol):
    def validate(self, *, upload_only: bool = False) -> None: ...

    async def pull(self, host: Host, job: Job, destination: Path, emit: EventSink) -> None: ...

    async def upload(self, archive: Path, destination: str, emit: EventSink) -> None: ...

    async def delete(self, destination: str) -> None: ...


class RcloneBackend:
    def __init__(self, config: Config):
        self.config = config

    def validate(self, *, upload_only: bool = False) -> None:
        binaries = [self.config.rclone_binary]
        paths = [self.config.rclone_config]
        if not upload_only:
            binaries.append(self.config.ssh_binary)
            for host in self.config.hosts.values():
                paths.extend([host.identity_file, host.ssh_config])
        for binary in binaries:
            if shutil.which(binary) is None:
                raise TransferError(f"executable not found: {binary}")
        for path in paths:
            if path is not None and not path.is_file():
                raise TransferError(f"configuration/key file not found: {path}")

    def ssh_command(self, host: Host) -> str:
        args = [self.config.ssh_binary]
        if host.ssh_config:
            args += ["-F", str(host.ssh_config)]
        args += [
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=yes",
            "-o",
            f"ConnectTimeout={self.config.connect_timeout}",
            "-o",
            "ServerAliveInterval=15",
            "-o",
            "ServerAliveCountMax=3",
        ]
        if host.user:
            args += ["-l", host.user]
        if host.port:
            args += ["-p", str(host.port)]
        if host.identity_file:
            args += ["-i", str(host.identity_file), "-o", "IdentitiesOnly=yes"]
        args.append(host.address)
        if host.sftp_server_command:
            # Keep rclone in subsystem mode so its external SSH connections are
            # reusable; its server-command mode does not pool those connections.
            args = [
                sys.executable,
                "-m",
                "stashfleet.ssh_transport",
                host.sftp_server_command,
                *args,
            ]
        # Rclone's SpaceSepList uses space-delimited CSV, not shell/JSON escaping.
        output = io.StringIO()
        csv.writer(output, delimiter=" ", lineterminator="\n").writerow(args)
        return output.getvalue().rstrip("\n")

    def arguments(self, *operation: str) -> list[str]:
        args = [
            self.config.rclone_binary,
            *operation,
            "--use-json-log",
            "--stats",
            "1s",
            "--stats-log-level",
            "INFO",
            "--log-level",
            "INFO",
            "--retries",
            "1",
            "--low-level-retries",
            "3",
            "--contimeout",
            f"{self.config.connect_timeout}s",
            "--transfers",
            str(self.config.transfers),
            "--checkers",
            str(self.config.transfers),
            "--multi-thread-streams",
            "0",
        ]
        if self.config.rclone_config:
            args += ["--config", str(self.config.rclone_config)]
        if self.config.bandwidth_limit:
            args += ["--bwlimit", self.config.bandwidth_limit]
        return args

    def pull_arguments(self, host: Host, job: Job, destination: Path) -> list[str]:
        args = self.arguments("copy", f":sftp:{job.source}", str(destination))
        if self.config.require_case_sensitive:
            args += ["--local-case-sensitive"]
        args += [
            "--sftp-host",
            host.address,
            "--sftp-ssh",
            self.ssh_command(host),
            "--create-empty-src-dirs",
            "--sftp-skip-links",
            "--sftp-connections",
            str(2 * self.config.transfers + 1),
        ]
        if host.sftp_server_command:
            # Hash commands run separately from the custom SFTP server, potentially
            # with different permissions. Keep this transfer inside SFTP instead.
            args += ["--sftp-disable-hashcheck"]
        for pattern in job.excludes:
            args += ["--exclude", pattern]
        return args

    async def pull(self, host: Host, job: Job, destination: Path, emit: EventSink) -> None:
        await self._run(self.pull_arguments(host, job, destination), f"{job.host}/{job.name}", emit)

    async def upload(self, archive: Path, destination: str, emit: EventSink) -> None:
        await self._run(
            self.arguments("copyto", str(archive), destination, "--immutable"), "upload", emit
        )

    async def delete(self, destination: str) -> None:
        await self._run(self.arguments("deletefile", destination), "retention", lambda _: None)

    async def _run(self, args: list[str], task: str, emit: EventSink) -> None:
        tail: deque[str] = deque(maxlen=5)
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
            limit=1024 * 1024,
        )
        try:
            async with asyncio.timeout(self.config.transfer_timeout):
                assert proc.stdout is not None
                async for line in proc.stdout:
                    message = line.decode("utf-8", errors="replace").strip()
                    try:
                        data = json.loads(message)
                    except (ValueError, TypeError):
                        tail.append(message[:1000])
                        continue
                    if not isinstance(data, dict):
                        continue
                    if data.get("level", "").lower() in {"error", "fatal", "warning"}:
                        tail.append(str(data.get("msg", ""))[:1000])
                    stats = data.get("stats")
                    if isinstance(stats, dict):
                        emit(
                            Event(
                                task,
                                "transfer",
                                int(stats.get("bytes") or 0),
                                int(stats["totalBytes"]) if stats.get("totalBytes") else None,
                            )
                        )
                code = await proc.wait()
                if code:
                    raise TransferError(f"rclone exited {code}: {'; '.join(tail)}")
        except TimeoutError as exc:
            raise TransferError(f"transfer exceeded {self.config.transfer_timeout:g}s") from exc
        finally:
            # Kill the process group, including external SSH children, on cancellation/error.
            # Also clean up stray descendants if the parent exited before a pipe was closed.
            if proc.returncode is None:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), 3)
                except TimeoutError:
                    pass
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            await proc.wait()

    def describe_pull(self, host: Host, job: Job, destination: Path) -> str:
        return shlex.join(self.pull_arguments(host, job, destination))
