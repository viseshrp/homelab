"""Streaming ZIP construction with cooperative cancellation and atomic publication."""

import hashlib
import os
import stat
import threading
import zipfile
from pathlib import Path
from typing import Protocol

from .config import ArchiveConfig
from .events import Event, EventSink


class ArchiveBuilder(Protocol):
    def build(
        self,
        source: Path,
        destination: Path,
        config: ArchiveConfig,
        emit: EventSink,
        stop: threading.Event,
    ) -> str: ...


class ZipArchiver:
    def build(
        self,
        source: Path,
        destination: Path,
        config: ArchiveConfig,
        emit: EventSink,
        stop: threading.Event,
    ) -> str:
        method, level = config.options()
        files = []
        total = 0
        for directory, dirs, names in os.walk(source, followlinks=False):
            _cancelled(stop)
            for name in sorted(dirs + names):
                path = Path(directory) / name
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise ValueError(f"ZIP input must contain regular files/directories: {path}")
                files.append(path)
                if path.is_file():
                    total += path.stat().st_size
        emit(Event("archive", "archive", 0, total))
        partial = destination.with_suffix(".zip.partial")
        completed = 0
        try:
            with zipfile.ZipFile(
                partial,
                "x",
                compression=method,
                compresslevel=level,
                allowZip64=True,
                strict_timestamps=False,
            ) as output:
                for path in files:
                    _cancelled(stop)
                    relative = path.relative_to(source).as_posix()
                    if path.is_dir():
                        output.write(path, relative + "/")
                        continue
                    info = zipfile.ZipInfo.from_file(path, relative, strict_timestamps=False)
                    info.compress_type = method
                    # ZipInfo.compress_level becomes public in Python 3.13.
                    info._compresslevel = level
                    with (
                        path.open("rb") as incoming,
                        output.open(info, "w", force_zip64=True) as out,
                    ):
                        while chunk := incoming.read(1024 * 1024):
                            _cancelled(stop)
                            out.write(chunk)
                            completed += len(chunk)
                            emit(Event("archive", "archive", completed, total))
            digest = sha256(partial, stop)
            _cancelled(stop)
            partial.replace(destination)
            return digest
        finally:
            partial.unlink(missing_ok=True)


def _cancelled(stop: threading.Event) -> None:
    if stop.is_set():
        raise InterruptedError("archive operation cancelled")


def sha256(path: Path, stop: threading.Event) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            _cancelled(stop)
            digest.update(chunk)
    return digest.hexdigest()
