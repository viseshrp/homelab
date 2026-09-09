import pytest

from stashfleet import ssh_transport


def test_subsystem_translation_preserves_arguments(monkeypatch):
    command = "sudo -n /usr/lib/openssh/sftp-server -R"
    ssh = ["/usr/bin/ssh", "-i", "/key with spaces", "-l", "backup", "host.invalid"]
    monkeypatch.setattr(ssh_transport.sys, "argv", ["wrapper", command, *ssh, "-s", "sftp"])
    calls = []
    monkeypatch.setattr(ssh_transport.os, "execvp", lambda *args: calls.append(args))
    ssh_transport.main()
    assert calls == [(ssh[0], [*ssh, command])]


@pytest.mark.parametrize("tail", [[], ["md5sum", "/secret"], ["-s", "other"]])
def test_transport_rejects_non_sftp_requests(monkeypatch, tail):
    monkeypatch.setattr(ssh_transport.sys, "argv", ["wrapper", "server", "ssh", "host", *tail])

    def forbidden(*args):
        pytest.fail("non-SFTP request must not execute")

    monkeypatch.setattr(ssh_transport.os, "execvp", forbidden)
    with pytest.raises(SystemExit, match="only the SFTP subsystem"):
        ssh_transport.main()
