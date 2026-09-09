import asyncio
import json
import signal
from dataclasses import replace

import pytest
from click.testing import CliRunner

from stashfleet import ArchiveConfig, CloudConfig, ConfigError, Job, load_config
from stashfleet.cli import main, run_async
from stashfleet.demo import create_demo
from stashfleet.state import validate_run_id


def test_example_and_local_paths(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("""destination = "data"
[hosts.example]
address = "example.invalid"
[[jobs]]
name = "config"
host = "example"
source = "/srv/config"
""")
    config = load_config(path)
    assert config.destination == tmp_path / "data"
    assert config.hosts["example"].user is None
    path.write_text("require_case_sensitive = true\n" + path.read_text())
    assert load_config(path).require_case_sensitive is True


@pytest.mark.parametrize("command", ["", " ", "bad\ncommand", "bad\x00command", 42])
def test_invalid_sftp_server_command(tmp_path, command):
    config, _ = create_demo(tmp_path / "demo")
    host = replace(config.hosts["alpha"], sftp_server_command=command)
    with pytest.raises(ConfigError, match="SFTP server command"):
        replace(config, hosts={**config.hosts, "alpha": host}).validate()


@pytest.mark.parametrize(
    "text",
    [
        'destination = "data"\nunknown = true',
        'destination = "data"\n[hosts]\nalpha = "bad"',
        'destination = "data"\n[runner]\nparallel_hosts = true',
    ],
)
def test_invalid_toml_schema(tmp_path, text):
    path = tmp_path / "config.toml"
    path.write_text(text)
    with pytest.raises(ConfigError):
        load_config(path)


@pytest.mark.parametrize(
    "compression,level",
    [
        ("invalid", None),
        ("store", 1),
        ("lzma", 5),
        ("deflate", 10),
        ("bzip2", 0),
        ("deflate", True),
    ],
)
def test_invalid_compression(compression, level):
    with pytest.raises(ConfigError):
        ArchiveConfig(compression, level).options()


def test_invalid_destinations(tmp_path):
    config, _ = create_demo(tmp_path / "demo")
    for job in (Job("../escape", "alpha", "/source"), Job("x", "alpha", "relative")):
        with pytest.raises(ConfigError):
            replace(config, jobs=(job,)).validate()
    with pytest.raises(ConfigError, match="duplicate"):
        replace(config, jobs=(config.jobs[0], replace(config.jobs[0], name="CONFIG"))).validate()
    with pytest.raises(ValueError):
        validate_run_id("../../outside")


@pytest.mark.parametrize(
    "destination,expected",
    [
        ("archive:", "archive:sample.zip"),
        ("archive:/", "archive:/sample.zip"),
        ("archive:/backups", "archive:/backups/sample.zip"),
        ("archive:/backups/", "archive:/backups/sample.zip"),
        ("archive:backups", "archive:backups/sample.zip"),
        ("archive:backups/", "archive:backups/sample.zip"),
        ("archive:backups//", "archive:backups//sample.zip"),
    ],
)
def test_cloud_target_preserves_remote_path(destination, expected):
    assert CloudConfig(True, destination).target("sample.zip") == expected


@pytest.mark.parametrize("fail", [False, True])
def test_cli_restores_previous_sigterm_handler(fail):
    original = signal.getsignal(signal.SIGTERM)

    def previous(*args):
        pytest.fail("previous signal handler should not be called")

    async def operation():
        if fail:
            raise ValueError("fake failure")
        return "finished"

    signal.signal(signal.SIGTERM, previous)
    try:
        if fail:
            with pytest.raises(ValueError, match="fake failure"):
                run_async(operation())
        else:
            assert run_async(operation()) == "finished"
        assert signal.getsignal(signal.SIGTERM) is previous
    finally:
        signal.signal(signal.SIGTERM, original)


def test_cli_demo_no_processes_or_network(tmp_path, monkeypatch):
    async def forbidden(*args, **kwargs):
        pytest.fail("demo must not launch subprocesses")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    result = CliRunner().invoke(main, ["demo", "--directory", str(tmp_path / "demo"), "--plain"])
    assert result.exit_code == 0, result.output
    assert "complete" in result.output
    assert len(list((tmp_path / "demo" / "fake-cloud").glob("*.zip"))) == 1


def test_cli_dry_run_never_writes_or_executes(tmp_path, monkeypatch):
    path = tmp_path / "config.toml"
    path.write_text("""destination = "must-not-exist"
[hosts.alpha]
address = "alpha.invalid"
[[jobs]]
name = "config"
host = "alpha"
source = "/config"
""")

    async def forbidden(*args, **kwargs):
        pytest.fail("dry run must not launch processes")

    monkeypatch.setattr(asyncio, "create_subprocess_exec", forbidden)
    result = CliRunner().invoke(main, ["run", "--config", str(path), "--dry-run"])
    assert result.exit_code == 0, result.output
    assert "StrictHostKeyChecking=yes" in result.output
    assert not (tmp_path / "must-not-exist").exists()


@pytest.mark.parametrize("json_events", [False, True])
def test_dry_run_previews_cloud_archive_retention_without_side_effects(
    tmp_path, monkeypatch, json_events
):
    path = tmp_path / "config.toml"
    path.write_text("""destination = "must-not-exist"
[hosts.alpha]
address = "alpha.invalid"
[[jobs]]
name = "config"
host = "alpha"
source = "/config"
[archive]
compression = "bzip2"
level = 4
[cloud]
enabled = true
destination = "gdrive:"
[retention]
keep_local = 2
keep_cloud = 3
[rclone]
binary = "not-installed-rclone"
""")

    def forbidden(*args, **kwargs):
        pytest.fail("dry run must not validate binaries or run the backup")

    from stashfleet import RcloneBackend, Runner

    monkeypatch.setattr(Runner, "run", forbidden)
    monkeypatch.setattr(RcloneBackend, "validate", forbidden)
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    args = ["run", "--config", str(path), "--dry-run", "--parallel-hosts", "5"]
    if json_events:
        args.append("--json-events")
    result = CliRunner().invoke(main, args)
    assert result.exit_code == 0, result.output
    if json_events:
        plan = json.loads(result.output)
        assert plan["dry_run"] is True
        assert plan["parallel_hosts"] == 5
        assert plan["archive"]["compression"] == "bzip2"
        assert plan["archive"]["level"] == 4
        assert plan["upload"][1] == "copyto"
        assert plan["upload"][3] == "gdrive:stashfleet-<run-id>.zip"
        assert plan["retention"] == {"keep_local": 2, "keep_cloud": 3}
    else:
        assert "DRY RUN" in result.output
        assert "ZIP:" in result.output
        assert "Upload:" in result.output
        assert "keep newest 2 completed runs" in result.output
        assert "keep newest 3 uploaded ZIPs" in result.output
    assert not (tmp_path / "must-not-exist").exists()
    after = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    assert before == after
