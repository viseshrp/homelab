"""Orchestration independent of the CLI, UI, and transfer implementation."""

import asyncio
import json
import shutil
import threading
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import partial
from pathlib import Path
from typing import TypeVar

from . import state
from .archive import ArchiveBuilder, ZipArchiver, sha256
from .backend import Backend, RcloneBackend
from .config import Config
from .events import Event, EventSink, discard

T = TypeVar("T")


@dataclass(frozen=True)
class RunResult:
    run_id: str
    status: str
    archive: Path | None
    errors: tuple[str, ...]

    @property
    def success(self) -> bool:
        return self.status == "complete" and not self.errors


class Runner:
    def __init__(
        self,
        config: Config,
        *,
        backend: Backend | None = None,
        archiver: ArchiveBuilder | None = None,
        emit: EventSink = discard,
    ):
        config.validate()
        self.config = config
        self.backend = backend if backend is not None else RcloneBackend(config)
        self.archiver = archiver if archiver is not None else ZipArchiver()
        self.emit = emit
        self.root = config.destination

    def _archive_path(self, run_id: str) -> Path:
        return self.root / "runs" / run_id / f"stashfleet-{run_id}.zip"

    def _cloud_target(self, run_id: str) -> str:
        return self.config.cloud.target(f"stashfleet-{run_id}.zip")

    def _result(self, manifest: dict) -> RunResult:
        archive = self._archive_path(manifest["id"])
        return RunResult(
            manifest["id"],
            manifest["status"],
            archive if archive.exists() else None,
            tuple(manifest["errors"]),
        )

    async def run(self) -> RunResult:
        self.backend.validate()
        with state.run_lock(self.root):
            run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ-") + uuid.uuid4().hex[:8]
            data = self.root / "runs" / run_id / "data"
            data.mkdir(parents=True, mode=0o700)
            manifest = {
                "schema": 1,
                "id": run_id,
                "status": "pulling",
                "errors": [],
                "started_at": datetime.now(UTC).isoformat(),
                "finished_at": None,
                "cloud_target": self._cloud_target(run_id) if self.config.cloud.enabled else None,
                "cloud_state": "pending" if self.config.cloud.enabled else "disabled",
                "archive_sha256": None,
                "jobs": [
                    {
                        "host": j.host,
                        "name": j.name,
                        "source": j.source,
                        "excludes": list(j.excludes),
                        "status": "queued",
                    }
                    for j in self.config.jobs
                ],
            }
            state.save(self.root, manifest)
            try:
                await self._pull_all(data, manifest)
                if manifest["errors"]:
                    manifest["status"] = "failed"
                    return self._result(manifest)
                manifest["status"] = "archiving"
                state.save(self.root, manifest)
                # This manifest describes the source set, not a filesystem/database snapshot.
                (data / "manifest.json").write_text(
                    json.dumps(
                        {
                            "schema": 1,
                            "run_id": run_id,
                            "jobs": manifest["jobs"],
                            "compression": self.config.archive.compression,
                        },
                        indent=2,
                    )
                    + "\n"
                )
                archive = self._archive_path(run_id)
                loop = asyncio.get_running_loop()
                manifest["archive_sha256"] = await self._thread(
                    lambda stop: self.archiver.build(
                        data,
                        archive,
                        self.config.archive,
                        lambda event: loop.call_soon_threadsafe(self.emit, event),
                        stop,
                    )
                )
                self.emit(Event("archive", "done", message="ZIP complete"))
                if self.config.cloud.enabled:
                    await self._upload(manifest)
                else:
                    manifest["status"] = "complete"
                state.save(self.root, manifest)
                await self._retain(manifest)
            except asyncio.CancelledError:
                # A complete ZIP is reusable even when cancellation interrupts cloud upload.
                manifest["status"] = (
                    "cloud_pending"
                    if manifest["archive_sha256"] and self.config.cloud.enabled
                    else "cancelled"
                )
                for job in manifest["jobs"]:
                    if job["status"] in {"queued", "pulling"}:
                        job["status"] = "cancelled"
                raise
            except Exception as exc:
                manifest["status"] = (
                    "cloud_pending"
                    if manifest["archive_sha256"] and self.config.cloud.enabled
                    else "failed"
                )
                manifest["errors"].append(str(exc))
                self.emit(Event("run", "failed", message=str(exc)))
            finally:
                manifest["finished_at"] = datetime.now(UTC).isoformat()
                state.save(self.root, manifest)
            return self._result(manifest)

    async def _pull_all(self, data: Path, manifest: dict) -> None:
        semaphore = asyncio.Semaphore(self.config.parallel_hosts)

        async def host_worker(host_name: str) -> None:
            async with semaphore:
                for job, record in zip(self.config.jobs, manifest["jobs"], strict=True):
                    if job.host != host_name:
                        continue
                    task = f"{job.host}/{job.name}"
                    destination = data / job.host / job.name
                    destination.mkdir(parents=True, mode=0o700)
                    record["status"] = "pulling"
                    state.save(self.root, manifest)
                    try:
                        await self._attempt(
                            task,
                            partial(
                                self.backend.pull,
                                self.config.hosts[job.host],
                                job,
                                destination,
                                self.emit,
                            ),
                        )
                        record["status"] = "complete"
                        self.emit(Event(task, "done"))
                    except Exception as exc:
                        record["status"] = "failed"
                        record["error"] = str(exc)
                        manifest["errors"].append(f"{task}: {exc}")
                        self.emit(Event(task, "failed", message=str(exc)))
                    state.save(self.root, manifest)

        # Expected job errors are caught above; TaskGroup still propagates cancellation.
        async with asyncio.TaskGroup() as group:
            for name in dict.fromkeys(j.host for j in self.config.jobs):
                group.create_task(host_worker(name))

    async def _attempt(self, task: str, action: Callable) -> None:
        for attempt in range(self.config.attempts):
            self.emit(Event(task, "started", message=f"attempt {attempt + 1}"))
            try:
                async with asyncio.timeout(self.config.transfer_timeout):
                    await action()
                return
            except (OSError, RuntimeError, TimeoutError) as exc:
                if attempt + 1 == self.config.attempts:
                    raise
                self.emit(Event(task, "retry", message=str(exc)))
                await asyncio.sleep(min(self.config.retry_delay * 2**attempt, 60))

    async def _upload(self, manifest: dict) -> None:
        manifest["status"] = "cloud_pending"
        state.save(self.root, manifest)
        await self._attempt(
            "upload",
            lambda: self.backend.upload(
                self._archive_path(manifest["id"]),
                manifest["cloud_target"],
                self.emit,
            ),
        )
        manifest["cloud_state"] = "uploaded"
        manifest["status"] = "complete"
        self.emit(Event("upload", "done"))

    async def retry_upload(self, run_id: str) -> RunResult:
        """Reuse a complete, SHA-256-verified ZIP; never contact source hosts."""
        self.backend.validate()
        with state.run_lock(self.root):
            manifest = state.read(self.root, run_id)
            if not self.config.cloud.enabled or manifest["cloud_target"] != self._cloud_target(
                run_id
            ):
                raise ValueError("enable the original cloud destination before retrying")
            if manifest["status"] != "cloud_pending" or not manifest.get("archive_sha256"):
                raise ValueError("run does not have a pending upload with a complete ZIP")
            archive = self._archive_path(run_id)
            if archive.is_symlink():
                raise ValueError("archive must not be a symlink")
            digest = await self._thread(lambda stop: sha256(archive, stop))
            if digest != manifest["archive_sha256"]:
                raise ValueError("archive checksum changed; refusing upload")
            manifest["errors"] = []
            try:
                await self._upload(manifest)
                state.save(self.root, manifest)
                await self._retain(manifest)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                manifest["errors"].append(str(exc))
            finally:
                manifest["finished_at"] = datetime.now(UTC).isoformat()
                state.save(self.root, manifest)
            return self._result(manifest)

    async def _thread(self, action: Callable[[threading.Event], T]) -> T:
        stop = threading.Event()
        task = asyncio.create_task(asyncio.to_thread(action, stop))
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            stop.set()
            try:
                await task
            except Exception:
                pass
            raise

    async def _retain(self, current: dict) -> None:
        """Only remove this destination's recorded, completed backups. Zero keeps all."""
        try:
            # A retried older run may itself be outside retention. Keep its in-memory
            # flags in sync so the caller's final save cannot undo deletion records.
            records = [current if r["id"] == current["id"] else r for r in state.history(self.root)]
            complete = [r for r in records if r["status"] == "complete"]
            if self.config.cloud.enabled and self.config.keep_cloud:
                uploaded = [
                    r
                    for r in complete
                    if r.get("cloud_state") == "uploaded"
                    and r.get("cloud_target") == self._cloud_target(r["id"])
                ]
                for old in uploaded[self.config.keep_cloud :]:
                    await self._attempt(
                        "retention", partial(self.backend.delete, old["cloud_target"])
                    )
                    old["cloud_state"] = "deleted"
                    state.save(self.root, old)
            if self.config.keep_local:
                for old in complete[self.config.keep_local :]:
                    if old.get("local_deleted"):
                        continue
                    path = self.root / "runs" / state.validate_run_id(old["id"])
                    if path.is_symlink():
                        raise ValueError(f"refusing to prune symlink: {path}")
                    if path.exists():
                        await self._thread(lambda stop, path=path: shutil.rmtree(path))
                    old["local_deleted"] = True
                    state.save(self.root, old)
        except Exception as exc:
            current["errors"].append(f"retention: {exc}")
            self.emit(Event("retention", "failed", message=str(exc)))
