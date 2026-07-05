import os

from incident_intelligencep_prj1.main import is_server_enabled


def test_server_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SERVE", raising=False)
    assert is_server_enabled() is False


def test_server_enabled_when_requested(monkeypatch):
    monkeypatch.setenv("SERVE", "1")
    assert is_server_enabled() is True
