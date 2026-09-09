"""Network-free example backend, also useful for integration tests."""

import asyncio
import fnmatch
import shutil
from pathlib import Path

from .config import CloudConfig, Config, Host, Job
from .events import Event, EventSink


class FakeBackend:
    """Copies explicit local fixtures. Never launches executables or opens sockets."""

    def __init__(self, cloud: Path):
        self.cloud = cloud

    def validate(self, *, upload_only: bool = False) -> None:
        pass

    async def pull(self, host: Host, job: Job, destination: Path, emit: EventSink) -> None:
        source = Path(job.source)
        if not source.is_dir():
            raise FileNotFoundError(source)
        files = []
        for path in sorted(source.rglob("*")):
            relative = path.relative_to(source)
            if any(fnmatch.fnmatch(relative.as_posix(), pattern) for pattern in job.excludes):
                continue
            if path.is_symlink():
                raise ValueError("fake backend refuses symlinks")
            target = destination / relative
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                files.append((path, target))
        total = sum(source.stat().st_size for source, _ in files)
        done = 0
        for source, target in files:
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as incoming, target.open("wb") as out:
                while chunk := incoming.read(64 * 1024):
                    out.write(chunk)
                    done += len(chunk)
                    emit(Event(f"{job.host}/{job.name}", "transfer", done, total))
                    await asyncio.sleep(0)

    async def upload(self, archive: Path, destination: str, emit: EventSink) -> None:
        self.cloud.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(archive, self.cloud / destination.rsplit("/", 1)[-1])
        emit(Event("upload", "transfer", archive.stat().st_size, archive.stat().st_size))

    async def delete(self, destination: str) -> None:
        (self.cloud / destination.rsplit("/", 1)[-1]).unlink(missing_ok=True)


def create_demo(directory: Path) -> tuple[Config, FakeBackend]:
    # Refuse an existing directory so fixtures cannot overwrite user files.
    directory.mkdir(parents=True, exist_ok=False)
    hosts = {}
    jobs = []
    for name in ("alpha", "beta"):
        source = directory / "fixtures" / name
        source.mkdir(parents=True)
        (source / "config.txt").write_text(f"Fake configuration for {name}\n" * 4000)
        (source / "empty").mkdir()
        hosts[name] = Host(f"{name}.invalid")
        jobs.append(Job("config", name, str(source)))
    config = Config(
        destination=directory / "backups",
        hosts=hosts,
        jobs=tuple(jobs),
        cloud=CloudConfig(True, "fake:backups"),
    )
    return config, FakeBackend(directory / "fake-cloud")
