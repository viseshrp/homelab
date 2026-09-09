"""Local run manifests and a process lock. Supported platforms: Linux and macOS."""

import fcntl
import json
import re
from contextlib import contextmanager
from pathlib import Path


class RunLocked(RuntimeError):
    pass


def validate_run_id(run_id: str) -> str:
    if not re.fullmatch(r"\d{8}T\d{12}Z-[a-f0-9]{8}", run_id):
        raise ValueError("invalid run ID")
    return run_id


@contextmanager
def run_lock(root: Path):
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / ".lock").open("a") as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RunLocked(f"another stashfleet run owns {root}") from exc
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def save(root: Path, manifest: dict) -> None:
    directory = root / "history"
    directory.mkdir(exist_ok=True, mode=0o700)
    path = directory / f"{validate_run_id(manifest['id'])}.json"
    partial = path.with_suffix(".tmp")
    partial.write_text(json.dumps(manifest, indent=2) + "\n")
    partial.replace(path)


def read(root: Path, run_id: str) -> dict:
    path = root / "history" / f"{validate_run_id(run_id)}.json"
    value = json.loads(path.read_text())
    if value.get("id") != run_id or value.get("schema") != 1:
        raise ValueError(f"invalid run manifest: {path}")
    return value


def history(root: Path) -> list[dict]:
    return [
        read(root, path.stem) for path in sorted((root / "history").glob("*.json"), reverse=True)
    ]
