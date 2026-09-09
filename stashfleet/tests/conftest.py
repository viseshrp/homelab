import socket

import pytest


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    """Any accidental server/cloud connection from package code fails the test."""

    def forbidden(*args, **kwargs):
        pytest.fail("network access is forbidden in Stashfleet tests")

    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
