import asyncio
import json
import threading
import zipfile
from dataclasses import replace

import pytest

from stashfleet import ArchiveConfig, CloudConfig, Config, Host, Job, Runner, ZipArchiver, state
from stashfleet.demo import FakeBackend


def setup(tmp_path, **options):
    jobs = []
    for name in ("alpha", "beta", "gamma"):
        source = tmp_path / "source" / name
        source.mkdir(parents=True)
        (source / "hello.txt").write_text(name * 10000)
        (source / "empty").mkdir()
        jobs.append(Job("config", name, str(source)))
    config = Config(
        destination=tmp_path / "backups",
        hosts={j.host: Host(f"{j.host}.invalid") for j in jobs},
        jobs=tuple(jobs),
        attempts=2,
        retry_delay=0,
        cloud=CloudConfig(True, "fake:backups"),
        **options,
    )
    return config, FakeBackend(tmp_path / "cloud")


def test_full_flow_archive_contents_and_events(tmp_path):
    config, backend = setup(tmp_path)
    events = []
    result = asyncio.run(Runner(config, backend=backend, emit=events.append).run())
    assert result.success
    with zipfile.ZipFile(result.archive) as archive:
        assert archive.testzip() is None
        assert archive.read("alpha/config/hello.txt") == b"alpha" * 10000
        assert "beta/config/empty/" in archive.namelist()
        manifest = json.loads(archive.read("manifest.json"))
        assert len(manifest["jobs"]) == 3
    assert (backend.cloud / result.archive.name).read_bytes() == result.archive.read_bytes()
    assert state.read(config.destination, result.run_id)["cloud_state"] == "uploaded"
    assert {e.task for e in events} >= {"alpha/config", "archive", "upload"}


def test_host_parallelism_and_sequential_folders(tmp_path):
    config, _ = setup(tmp_path)
    config = replace(config, jobs=(*config.jobs, replace(config.jobs[0], name="second")))

    class Observed(FakeBackend):
        active = 0
        peak = 0
        hosts = set()

        async def pull(self, host, job, destination, emit):
            assert job.host not in self.hosts
            self.hosts.add(job.host)
            self.active += 1
            self.peak = max(self.peak, self.active)
            await asyncio.sleep(0.01)
            await super().pull(host, job, destination, emit)
            self.active -= 1
            self.hosts.remove(job.host)

    backend = Observed(tmp_path / "cloud")
    assert asyncio.run(Runner(config, backend=backend).run()).success
    assert backend.peak == config.parallel_hosts


def test_exhausted_pull_continues_other_hosts_and_skips_archive(tmp_path):
    config, _ = setup(tmp_path)

    class Broken(FakeBackend):
        failures = 0

        async def pull(self, host, job, destination, emit):
            if job.host == "alpha":
                self.failures += 1
                raise RuntimeError("fake offline host")
            await super().pull(host, job, destination, emit)

        async def upload(self, *args):
            pytest.fail("must not upload incomplete runs")

    backend = Broken(tmp_path / "cloud")
    result = asyncio.run(Runner(config, backend=backend).run())
    assert result.status == "failed"
    assert result.archive is None
    assert backend.failures == 2
    manifest = state.read(config.destination, result.run_id)
    assert [j["status"] for j in manifest["jobs"]] == ["failed", "complete", "complete"]


def test_upload_retry_reuses_zip_without_pulls_and_rejects_tampering(tmp_path):
    config, _ = setup(tmp_path)

    class UploadFails(FakeBackend):
        async def upload(self, *args):
            raise RuntimeError("fake cloud offline")

    result = asyncio.run(Runner(config, backend=UploadFails(tmp_path / "cloud")).run())
    assert result.status == "cloud_pending"
    original = result.archive.read_bytes()

    class NoPulls(FakeBackend):
        async def pull(self, *args):
            pytest.fail("upload retry must not pull")

    runner = Runner(config, backend=NoPulls(tmp_path / "cloud"))
    result.archive.write_bytes(original + b"tampering")
    with pytest.raises(ValueError, match="checksum"):
        asyncio.run(runner.retry_upload(result.run_id))
    result.archive.write_bytes(original)
    uploaded = asyncio.run(runner.retry_upload(result.run_id))
    assert uploaded.success
    assert uploaded.archive.read_bytes() == original


def test_retention_only_prunes_managed_complete_backups(tmp_path):
    config, backend = setup(tmp_path, keep_local=1, keep_cloud=1)
    backend.cloud.mkdir()
    unrelated = backend.cloud / "unrelated.zip"
    unrelated.write_bytes(b"not managed")
    first = asyncio.run(Runner(config, backend=backend).run())
    second = asyncio.run(Runner(config, backend=backend).run())
    assert first.success and second.success
    assert not first.archive.exists()
    assert second.archive.exists()
    assert unrelated.exists()
    assert not (backend.cloud / first.archive.name).exists()
    old = state.read(config.destination, first.run_id)
    assert old["local_deleted"] and old["cloud_state"] == "deleted"


def test_pending_upload_not_pruned_by_next_success(tmp_path):
    config, backend = setup(tmp_path, keep_local=1, keep_cloud=1)

    class Failing(FakeBackend):
        async def upload(self, *args):
            raise RuntimeError("cloud unavailable")

    pending = asyncio.run(Runner(config, backend=Failing(tmp_path / "cloud")).run())
    for _ in range(2):
        assert asyncio.run(Runner(config, backend=backend).run()).success
    assert pending.archive.exists()
    assert state.read(config.destination, pending.run_id)["status"] == "cloud_pending"

    retried = asyncio.run(Runner(config, backend=backend).retry_upload(pending.run_id))
    assert retried.success
    old = state.read(config.destination, pending.run_id)
    assert old["local_deleted"]
    assert old["cloud_state"] == "deleted"


def test_local_only_and_lock(tmp_path):
    config, backend = setup(tmp_path)
    config = replace(config, cloud=CloudConfig())
    with state.run_lock(config.destination):
        with pytest.raises(state.RunLocked):
            asyncio.run(Runner(config, backend=backend).run())
    assert asyncio.run(Runner(config, backend=backend).run()).success
    assert not backend.cloud.exists()


def test_cancel_stops_workers_and_releases_lock(tmp_path):
    config, _ = setup(tmp_path)

    class Blocking(FakeBackend):
        active = 0

        def __init__(self, cloud):
            super().__init__(cloud)
            self.started = asyncio.Event()

        async def pull(self, *args):
            self.active += 1
            self.started.set()
            try:
                await asyncio.sleep(60)
            finally:
                self.active -= 1

    backend = Blocking(tmp_path / "cloud")

    async def exercise():
        task = asyncio.create_task(Runner(config, backend=backend).run())
        await backend.started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert backend.active == 0

    asyncio.run(exercise())
    with state.run_lock(config.destination):
        assert state.history(config.destination)[0]["status"] == "cancelled"


@pytest.mark.parametrize(
    "method,level,expected",
    [
        ("store", None, zipfile.ZIP_STORED),
        ("deflate", 0, zipfile.ZIP_DEFLATED),
        ("deflate", 9, zipfile.ZIP_DEFLATED),
        ("bzip2", 1, zipfile.ZIP_BZIP2),
        ("lzma", None, zipfile.ZIP_LZMA),
    ],
)
def test_compression_roundtrip(tmp_path, method, level, expected):
    source = tmp_path / "data"
    source.mkdir()
    content = b"compress me " * 10000
    (source / "data.txt").write_bytes(content)
    target = tmp_path / "output.zip"
    ZipArchiver().build(
        source, target, ArchiveConfig(method, level), lambda _: None, threading.Event()
    )
    with zipfile.ZipFile(target) as archive:
        assert archive.read("data.txt") == content
        assert archive.getinfo("data.txt").compress_type == expected
        if method == "deflate" and level == 9:
            assert archive.getinfo("data.txt").compress_size < len(content) // 10


def test_archive_rejects_symlinks_and_does_not_publish_partial(tmp_path):
    source = tmp_path / "data"
    source.mkdir()
    secret = tmp_path / "outside.txt"
    secret.write_text("outside source")
    (source / "link").symlink_to(secret)
    target = tmp_path / "output.zip"
    with pytest.raises(ValueError, match="regular files"):
        ZipArchiver().build(source, target, ArchiveConfig(), lambda _: None, threading.Event())
    assert not target.exists()
    assert not target.with_suffix(".zip.partial").exists()


def test_archive_cancellation_does_not_publish_partial(tmp_path):
    source = tmp_path / "data"
    source.mkdir()
    (source / "data.txt").write_bytes(b"data" * 300000)
    stop = threading.Event()
    target = tmp_path / "output.zip"

    def emit(event):
        if event.completed:
            stop.set()

    with pytest.raises(InterruptedError):
        ZipArchiver().build(source, target, ArchiveConfig(), emit, stop)
    assert not target.exists()
    assert not target.with_suffix(".zip.partial").exists()
