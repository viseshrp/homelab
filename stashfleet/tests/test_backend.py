import asyncio
import csv
import json
import os
import signal
import sys
import textwrap
from dataclasses import replace

import pytest

from stashfleet import Config, Host, Job, RcloneBackend, TransferError


@pytest.fixture
def fake_rclone(tmp_path):
    """A local Python stub. It never invokes SSH or a real transfer tool."""
    binary = tmp_path / "fake-rclone"
    binary.write_text(
        f"#!{sys.executable}\n"
        + textwrap.dedent("""
        import json
        import os
        import signal
        import subprocess
        import sys
        import time
        from pathlib import Path

        Path(os.environ["FAKE_ARGS"]).write_text(json.dumps(sys.argv[1:]))
        mode = os.environ.get("FAKE_MODE", "success")
        if mode == "fail":
            print(json.dumps({"level": "error", "msg": "fake permission denied"}), flush=True)
            sys.exit(5)
        if mode == "block":
            child_code = (
                "import signal,time,sys; from pathlib import Path; "
                "signal.signal(signal.SIGTERM, lambda *_: "
                "(Path(sys.argv[1]).write_text('terminated'), sys.exit(0))); "
                "Path(sys.argv[2]).write_text('ready'); time.sleep(60)"
            )
            child = subprocess.Popen([sys.executable, "-c", child_code,
                                      os.environ["FAKE_STOP"], os.environ["FAKE_READY"]])
            Path(os.environ["FAKE_PID"]).write_text(str(child.pid))
            # Reap our child when the group is terminated.
            def stop(*_):
                child.wait(timeout=2)
                sys.exit(0)
            signal.signal(signal.SIGTERM, stop)
            time.sleep(60)
        print("not JSON, like an SSH diagnostic", flush=True)
        print(json.dumps({"stats": {"bytes": 25, "totalBytes": 100}}), flush=True)
        print(json.dumps({"stats": {"bytes": 100, "totalBytes": 100}}), flush=True)
    """)
    )
    binary.chmod(0o700)
    return binary


def config(tmp_path, binary):
    return Config(
        destination=tmp_path / "backups",
        hosts={"alpha": Host("alpha.invalid")},
        jobs=(Job("config", "alpha", "/srv/config with spaces"),),
        rclone_binary=str(binary),
        ssh_binary=sys.executable,
        attempts=1,
    )


def test_argument_quoting_matches_rclone_csv_parser(tmp_path, fake_rclone):
    cfg = config(tmp_path, fake_rclone)
    host = Host(
        "host.invalid",
        user="backup",
        port=2222,
        identity_file=tmp_path / "keys with spaces" / 'ü"key',
        ssh_config=tmp_path / "ssh config",
    )
    backend = RcloneBackend(cfg)
    tokens = next(csv.reader([backend.ssh_command(host)], delimiter=" "))
    assert tokens[tokens.index("-i") + 1] == str(host.identity_file)
    assert tokens[tokens.index("-F") + 1] == str(host.ssh_config)
    assert "StrictHostKeyChecking=yes" in tokens
    assert "BatchMode=yes" in tokens
    assert tokens[-1] == host.address


def test_fake_process_progress_and_nonzero_exit(tmp_path, fake_rclone, monkeypatch):
    cfg = config(tmp_path, fake_rclone)
    args_file = tmp_path / "args.json"
    monkeypatch.setenv("FAKE_ARGS", str(args_file))
    backend = RcloneBackend(cfg)
    events = []
    asyncio.run(backend.pull(cfg.hosts["alpha"], cfg.jobs[0], tmp_path / "output", events.append))
    assert [(e.completed, e.total) for e in events] == [(25, 100), (100, 100)]
    args = json.loads(args_file.read_text())
    assert args[0] == "copy"
    assert args[1] == ":sftp:/srv/config with spaces"
    monkeypatch.setenv("FAKE_MODE", "fail")
    with pytest.raises(TransferError, match="fake permission denied"):
        asyncio.run(
            backend.pull(cfg.hosts["alpha"], cfg.jobs[0], tmp_path / "output", events.append)
        )


@pytest.mark.parametrize("cancel", [False, True])
def test_timeout_and_cancellation_stop_process_group(tmp_path, fake_rclone, monkeypatch, cancel):
    cfg = replace(config(tmp_path, fake_rclone), transfer_timeout=0.8)
    for key, name in [
        ("FAKE_ARGS", "args.json"),
        ("FAKE_STOP", "stopped"),
        ("FAKE_READY", "ready"),
        ("FAKE_PID", "pid"),
    ]:
        monkeypatch.setenv(key, str(tmp_path / name))
    monkeypatch.setenv("FAKE_MODE", "block")
    backend = RcloneBackend(cfg)

    async def exercise():
        task = asyncio.create_task(
            backend.pull(cfg.hosts["alpha"], cfg.jobs[0], tmp_path / "output", lambda _: None)
        )
        if cancel:
            # Bounded local-fixture polling only; this does not contact a host.
            for _ in range(100):
                if (tmp_path / "ready").exists():
                    break
                await asyncio.sleep(0.005)
            assert (tmp_path / "ready").exists()
            task.cancel()
        with pytest.raises(asyncio.CancelledError if cancel else TransferError):
            await task

    try:
        asyncio.run(exercise())
        assert (tmp_path / "stopped").read_text() == "terminated"
        pid = int((tmp_path / "pid").read_text())
        with pytest.raises(ProcessLookupError):
            os.kill(pid, 0)
    finally:
        # A failed test must not leave the deliberately sleeping fixture child alive.
        if (tmp_path / "pid").exists():
            try:
                os.kill(int((tmp_path / "pid").read_text()), signal.SIGKILL)
            except ProcessLookupError:
                pass
