"""Strict TOML configuration; relative local paths resolve beside the config file."""

import math
import re
import tomllib
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class Host:
    address: str
    user: str | None = None
    port: int | None = None
    identity_file: Path | None = None
    ssh_config: Path | None = None
    sftp_server_command: str | None = None


@dataclass(frozen=True)
class Job:
    name: str
    host: str
    source: str
    excludes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ArchiveConfig:
    compression: str = "deflate"
    level: int | None = None

    def options(self) -> tuple[int, int | None]:
        methods = {
            "store": (zipfile.ZIP_STORED, None),
            "deflate": (zipfile.ZIP_DEFLATED, 6),
            "bzip2": (zipfile.ZIP_BZIP2, 9),
            "lzma": (zipfile.ZIP_LZMA, None),
        }
        if not isinstance(self.compression, str) or self.compression not in methods:
            raise ConfigError("archive.compression must be store, deflate, bzip2, or lzma")
        method, default = methods[self.compression]
        module = {"deflate": "zlib", "bzip2": "bz2", "lzma": "lzma"}.get(self.compression)
        if module and getattr(zipfile, module) is None:
            raise ConfigError(f"this Python installation does not support {self.compression}")
        level = self.level if self.level is not None else default
        if self.compression in {"store", "lzma"} and level is not None:
            raise ConfigError(f"{self.compression} does not accept a compression level")
        if level is not None:
            minimum = 1 if self.compression == "bzip2" else 0
            if type(level) is not int or not minimum <= level <= 9:
                raise ConfigError(f"{self.compression} level must be {minimum}..9")
        return method, level


@dataclass(frozen=True)
class CloudConfig:
    enabled: bool = False
    destination: str = ""  # Configured rclone remote, e.g. gdrive:stashfleet

    def target(self, filename: str) -> str:
        separator = "" if self.destination.endswith((":", "/")) else "/"
        return f"{self.destination}{separator}{filename}"


@dataclass(frozen=True)
class Config:
    destination: Path
    hosts: dict[str, Host]
    jobs: tuple[Job, ...]
    parallel_hosts: int = 2
    transfers: int = 2
    attempts: int = 3
    retry_delay: float = 2.0
    connect_timeout: int = 15
    transfer_timeout: float = 3600.0
    rclone_binary: str = "rclone"
    ssh_binary: str = "ssh"
    rclone_config: Path | None = None
    bandwidth_limit: str | None = None
    archive: ArchiveConfig = field(default_factory=ArchiveConfig)
    cloud: CloudConfig = field(default_factory=CloudConfig)
    keep_local: int = 0
    keep_cloud: int = 0
    require_case_sensitive: bool = False

    def validate(self) -> None:
        if type(self.require_case_sensitive) is not bool:
            raise ConfigError("require_case_sensitive must be true or false")
        for name in ("parallel_hosts", "transfers", "attempts", "connect_timeout"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 1:
                raise ConfigError(f"{name} must be a positive integer")
        for name in ("retry_delay", "transfer_timeout"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ConfigError(f"{name} must be a number")
            if not math.isfinite(value) or value < 0 or (name == "transfer_timeout" and not value):
                raise ConfigError(f"invalid {name}")
        for name in ("keep_local", "keep_cloud"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ConfigError(f"{name} must be a nonnegative integer (0 keeps everything)")
        if not self.destination.is_absolute():
            raise ConfigError("destination must be absolute when using the Python API")
        if not self.jobs:
            raise ConfigError("at least one job is required")
        seen = set()
        for name, host in self.hosts.items():
            _name(name)
            if host.sftp_server_command is not None and (
                not isinstance(host.sftp_server_command, str)
                or not host.sftp_server_command.strip()
                or any(c in host.sftp_server_command for c in "\x00\r\n")
            ):
                raise ConfigError(f"invalid SFTP server command for {name}")
            if host.address is None:
                raise ConfigError(f"host {name} needs an address")
            for value in (host.address, host.user):
                if value is not None and (
                    not isinstance(value, str)
                    or not value
                    or value.startswith("-")
                    or any(c.isspace() or c in "\x00@" for c in value)
                ):
                    raise ConfigError(f"invalid SSH address/user for host {name}")
            if host.port is not None and (
                type(host.port) is not int or not 1 <= host.port <= 65535
            ):
                raise ConfigError(f"invalid SSH port for {name}")
        for job in self.jobs:
            _name(job.name)
            if job.host not in self.hosts:
                raise ConfigError(f"unknown host {job.host!r} in job {job.name}")
            key = (job.host.casefold(), job.name.casefold())
            if key in seen:
                raise ConfigError(f"duplicate destination for {job.host}/{job.name}")
            seen.add(key)
            if not isinstance(job.source, str) or not job.source.startswith("/"):
                raise ConfigError(f"source for {job.name} must be an absolute remote folder")
            if any(c in job.source for c in "\x00\r\n"):
                raise ConfigError("source contains a control character")
            if not all(isinstance(x, str) and "\x00" not in x for x in job.excludes):
                raise ConfigError("excludes must be strings")
        if len({name.casefold() for name in self.hosts}) != len(self.hosts):
            raise ConfigError("host names must be unique ignoring case")
        if type(self.cloud.enabled) is not bool:
            raise ConfigError("cloud.enabled must be true or false")
        if not isinstance(self.cloud.destination, str) or (
            self.cloud.enabled
            and not re.fullmatch(
                r"[A-Za-z0-9_][A-Za-z0-9_.-]*:[^\x00\r\n]*", self.cloud.destination
            )
        ):
            raise ConfigError("cloud.destination must be a named rclone remote:path")
        self.archive.options()


def _name(value: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise ConfigError("host/job names must be 1..64 letters, digits, underscores or hyphens")


def _table(value: Any, allowed: set[str], label: str) -> dict:
    if not isinstance(value, dict):
        raise ConfigError(f"{label} must be a TOML table")
    unknown = value.keys() - allowed
    if unknown:
        raise ConfigError(f"unknown {label} options: {', '.join(sorted(unknown))}")
    return value


def load_config(path: str | Path) -> Config:
    path = Path(path).expanduser().resolve()

    def local(value: str) -> Path:
        if not isinstance(value, str) or not value:
            raise ConfigError("local paths must be nonempty strings")
        expanded = Path(value).expanduser()
        return (path.parent / expanded).resolve()

    try:
        with path.open("rb") as stream:
            raw = tomllib.load(stream)
        _table(
            raw,
            {
                "destination",
                "hosts",
                "jobs",
                "runner",
                "rclone",
                "archive",
                "cloud",
                "retention",
                "require_case_sensitive",
            },
            "top-level",
        )
        hosts = {}
        for name, value in raw.get("hosts", {}).items():
            h = _table(
                value,
                {"address", "user", "port", "identity_file", "ssh_config", "sftp_server_command"},
                "host",
            )
            hosts[name] = Host(
                **{
                    **h,
                    "address": h.get("address", name),
                    **{k: local(h[k]) for k in ("identity_file", "ssh_config") if k in h},
                }
            )
        jobs = []
        for value in raw.get("jobs", []):
            j = _table(value, {"name", "host", "source", "excludes"}, "job")
            if not isinstance(j.get("excludes", []), list):
                raise ConfigError("job.excludes must be an array")
            jobs.append(Job(**{**j, "excludes": tuple(j.get("excludes", []))}))
        runner = _table(
            raw.get("runner", {}),
            {
                "parallel_hosts",
                "transfers",
                "attempts",
                "retry_delay",
                "connect_timeout",
                "transfer_timeout",
            },
            "runner",
        )
        rclone = _table(
            raw.get("rclone", {}),
            {
                "binary",
                "ssh_binary",
                "config",
                "bandwidth_limit",
            },
            "rclone",
        )
        for key, value in rclone.items():
            if not isinstance(value, str) or not value or "\x00" in value:
                raise ConfigError(f"rclone.{key} must be a nonempty string")
        archive = _table(raw.get("archive", {}), {"compression", "level"}, "archive")
        cloud = _table(raw.get("cloud", {}), {"enabled", "destination"}, "cloud")
        retention = _table(raw.get("retention", {}), {"keep_local", "keep_cloud"}, "retention")
        config = Config(
            destination=local(raw["destination"]),
            require_case_sensitive=raw.get("require_case_sensitive", False),
            hosts=hosts,
            jobs=tuple(jobs),
            **runner,
            **retention,
            archive=ArchiveConfig(**archive),
            cloud=CloudConfig(**cloud),
            rclone_binary=rclone.get("binary", "rclone"),
            ssh_binary=rclone.get("ssh_binary", "ssh"),
            rclone_config=local(rclone["config"]) if "config" in rclone else None,
            bandwidth_limit=rclone.get("bandwidth_limit"),
        )
        config.validate()
        return config
    except (KeyError, TypeError, AttributeError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"invalid configuration: {exc}") from exc
