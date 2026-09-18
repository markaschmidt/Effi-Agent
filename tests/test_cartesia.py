from __future__ import annotations

from services.cartesia import resolve_tts_config


def test_resolve_tts_defaults_to_cartesia(monkeypatch) -> None:
    monkeypatch.delenv("CARTESIA_MODEL", raising=False)
    monkeypatch.delenv("CARTESIA_VOICE_ID", raising=False)
    cfg = resolve_tts_config()
    assert cfg["provider"] == "cartesia"
    assert cfg["model"] == "cartesia/sonic-3"
    assert cfg["voice"]


def test_resolve_tts_uses_agent_env(monkeypatch) -> None:
    monkeypatch.setenv("CARTESIA_MODEL", "sonic-2")
    monkeypatch.setenv("CARTESIA_VOICE_ID", "voice-from-agent-env")
    cfg = resolve_tts_config()
    assert cfg["model"] == "cartesia/sonic-2"
    assert cfg["voice"] == "voice-from-agent-env"


def test_resolve_tts_prefixes_bare_model(monkeypatch) -> None:
    monkeypatch.setenv("CARTESIA_MODEL", "sonic-3")
    monkeypatch.setenv("CARTESIA_VOICE_ID", "abc")
    cfg = resolve_tts_config()
    assert cfg["model"] == "cartesia/sonic-3"
