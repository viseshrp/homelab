import asyncio
import csv
import json
import os
import shutil
import signal
import subprocess
import sys
import textwrap
import time
from dataclasses import replace
from pathlib import Path

import pytest

from stashfleet import CloudConfig, Config, Host, Job, RcloneBackend, Runner, TransferError, state
from stashfleet.demo import FakeBackend


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
        if parent_pid := os.environ.get("FAKE_PARENT_PID"):
            Path(parent_pid).write_text(str(os.getpid()))
        mode = os.environ.get("FAKE_MODE", "success")
        if mode == "fail":
            print(json.dumps({"level": "error", "msg": "fake permission denied"}), flush=True)
            sys.exit(5)
        if mode == "block":
            child_code = (
                "import signal,time,sys; from pathlib import Path; "
                "signal.signal(signal.SIGTERM, lambda *_: "
                "(Path(sys.argv[1]).write_text('terminated'), "
                "time.sleep(float(sys.argv[3])), sys.exit(0))); "
                "Path(sys.argv[2]).write_text('ready'); time.sleep(60)"
            )
            child = subprocess.Popen([sys.executable, "-c", child_code,
                                      os.environ["FAKE_STOP"], os.environ["FAKE_READY"],
                                      os.environ.get("FAKE_STOP_DELAY", "0")])
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


def test_custom_read_only_server_is_scoped_to_its_host(tmp_path, fake_rclone):
    cfg = config(tmp_path, fake_rclone)
    backend = RcloneBackend(cfg)
    command = "sudo -n /usr/lib/openssh/sftp-server -R"
    privileged = replace(cfg.hosts["alpha"], sftp_server_command=command)
    args = backend.pull_arguments(privileged, cfg.jobs[0], tmp_path / "output")
    ssh = next(csv.reader([args[args.index("--sftp-ssh") + 1]], delimiter=" "))
    assert ssh[:4] == [sys.executable, "-m", "stashfleet.ssh_transport", command]
    assert "--sftp-server-command" not in args
    assert "--sftp-disable-hashcheck" in args
    ordinary = backend.pull_arguments(cfg.hosts["alpha"], cfg.jobs[0], tmp_path / "other")
    assert "--sftp-server-command" not in ordinary
    assert "--sftp-disable-hashcheck" not in ordinary
    assert args[args.index("--sftp-connections") + 1] == str(2 * cfg.transfers + 1)
    assert args[args.index("--checkers") + 1] == str(cfg.transfers)
    assert "--sftp-skip-links" in args
    assert "--sftp-skip-links" in ordinary


def test_case_sensitive_destination_is_reported_to_rclone(tmp_path, fake_rclone):
    cfg = replace(config(tmp_path, fake_rclone), require_case_sensitive=True)
    args = RcloneBackend(cfg).pull_arguments(cfg.hosts["alpha"], cfg.jobs[0], tmp_path / "copy")
    assert "--local-case-sensitive" in args


def test_real_rclone_reuses_custom_sftp_connections_without_network(tmp_path):
    rclone = shutil.which("rclone")
    server = next(
        (
            p
            for p in ("/usr/libexec/sftp-server", "/usr/lib/openssh/sftp-server")
            if Path(p).is_file()
        ),
        None,
    )
    if not rclone or not server:
        pytest.skip("optional offline integration requires rclone and a local SFTP server")
    source = tmp_path / "source"
    source.mkdir()
    for index in range(100):
        (source / f"file-{index}.txt").write_text(f"fixture {index}")
    (source / "broken-link").symlink_to(source / "missing")
    (source / "file-link").symlink_to(source / "file-0.txt")
    connections = tmp_path / "connections"
    fake_ssh = tmp_path / "local-ssh"
    fake_ssh.write_text(
        f"#!{sys.executable}\n"
        "import os,sys\n"
        "assert sys.argv[-1] == 'local read-only SFTP'\n"
        f"with open({str(connections)!r}, 'a') as log: log.write(str(os.getpid()) + '\\n')\n"
        f"os.execv({server!r}, [{server!r}, '-R'])\n"
    )
    fake_ssh.chmod(0o700)
    empty_config = tmp_path / "rclone.conf"
    empty_config.write_text("")
    cfg = replace(
        config(tmp_path, rclone),
        ssh_binary=str(fake_ssh),
        rclone_config=empty_config,
        hosts={"alpha": Host("fixture.invalid", sftp_server_command="local read-only SFTP")},
        jobs=(Job("config", "alpha", str(source)),),
        transfer_timeout=20,
    )
    target = tmp_path / "copied"
    asyncio.run(RcloneBackend(cfg).pull(cfg.hosts["alpha"], cfg.jobs[0], target, lambda _: None))
    assert len(list(target.iterdir())) == 100
    for path in source.iterdir():
        if path.is_symlink():
            assert not (target / path.name).exists()
            continue
        assert (target / path.name).read_bytes() == path.read_bytes()
    assert 1 <= len(connections.read_text().splitlines()) <= 2 * cfg.transfers + 1


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


@pytest.mark.parametrize("missing", ["binary", "config"])
def test_upload_validation_still_requires_rclone_dependencies(tmp_path, fake_rclone, missing):
    cfg = config(tmp_path, fake_rclone)
    if missing == "binary":
        cfg = replace(cfg, rclone_binary=str(tmp_path / "missing-rclone"))
        message = "executable not found"
    else:
        cfg = replace(cfg, rclone_config=tmp_path / "missing-rclone.conf")
        message = "configuration/key file not found"
    with pytest.raises(TransferError, match=message):
        RcloneBackend(cfg).validate(upload_only=True)


@pytest.mark.parametrize("command", ["run", "retry-upload"])
def test_cli_sigterm_cleans_process_group_and_saves_state(tmp_path, fake_rclone, command):
    source = tmp_path / "source"
    source.mkdir()
    (source / "fixture.txt").write_text("local test data")
    cfg = config(tmp_path, fake_rclone)
    cfg = replace(
        cfg,
        jobs=(replace(cfg.jobs[0], source=str(source)),),
        cloud=CloudConfig(True, "fake:backups"),
    )
    config_path = tmp_path / "config.toml"
    config_path.write_text(f"""destination = {json.dumps(str(cfg.destination))}
[hosts.alpha]
address = "alpha.invalid"
[[jobs]]
name = "config"
host = "alpha"
source = {json.dumps(str(source))}
[runner]
attempts = 1
[rclone]
binary = {json.dumps(str(fake_rclone))}
ssh_binary = {json.dumps(sys.executable)}
[cloud]
enabled = true
destination = "fake:backups"
""")
    args = [sys.executable, "-m", "stashfleet", command]
    previous_finished = None
    if command == "retry-upload":

        class UploadFails(FakeBackend):
            async def upload(self, *args):
                raise RuntimeError("fake cloud offline")

        pending = asyncio.run(Runner(cfg, backend=UploadFails(tmp_path / "cloud")).run())
        assert pending.status == "cloud_pending"
        previous_finished = state.read(cfg.destination, pending.run_id)["finished_at"]
        args.append(pending.run_id)
    args += ["--config", str(config_path), "--plain"]
    markers = {
        "FAKE_ARGS": tmp_path / "args.json",
        "FAKE_STOP": tmp_path / "stopped",
        "FAKE_READY": tmp_path / "ready",
        "FAKE_PID": tmp_path / "child.pid",
        "FAKE_PARENT_PID": tmp_path / "parent.pid",
    }
    env = {
        **os.environ,
        **{key: str(path) for key, path in markers.items()},
        "FAKE_MODE": "block",
        "FAKE_STOP_DELAY": "0.3",
    }
    proc = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def wait_for_marker(key):
        deadline = time.monotonic() + 5
        while not markers[key].exists():
            assert proc.poll() is None, "CLI exited before the fixture was ready"
            assert time.monotonic() < deadline, f"fixture did not create {key}"
            time.sleep(0.01)

    try:
        wait_for_marker("FAKE_READY")
        proc.terminate()
        wait_for_marker("FAKE_STOP")
        # A second SIGTERM during cleanup must not cancel the cleanup itself.
        proc.terminate()
        stdout, stderr = proc.communicate(timeout=10)
        assert proc.returncode == 143, (stdout, stderr)
        assert b"Terminated." in stderr
        assert b"Traceback" not in stderr
        for key in ("FAKE_PID", "FAKE_PARENT_PID"):
            with pytest.raises(ProcessLookupError):
                os.kill(int(markers[key].read_text()), 0)
        with state.run_lock(cfg.destination):
            manifest = state.history(cfg.destination)[0]
        assert manifest["finished_at"]
        assert manifest["finished_at"] != previous_finished
        if command == "run":
            assert manifest["status"] == "cancelled"
            assert manifest["jobs"][0]["status"] == "cancelled"
            assert not list((cfg.destination / "runs").rglob("*.zip*"))
        else:
            assert manifest["status"] == "cloud_pending"
            assert manifest["cloud_state"] == "pending"
            assert pending.archive.exists()
    finally:
        # Kill only these temporary fixture processes if an assertion failed.
        if proc.poll() is None:
            proc.kill()
        proc.communicate(timeout=5)
        for key in ("FAKE_PARENT_PID", "FAKE_PID"):
            if markers[key].exists():
                try:
                    kill = os.killpg if key == "FAKE_PARENT_PID" else os.kill
                    kill(int(markers[key].read_text()), signal.SIGKILL)
                except ProcessLookupError:
                    pass


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
