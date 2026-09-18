from __future__ import annotations

import os

DEFAULT_MODEL = "cartesia/sonic-3"
DEFAULT_VOICE_ID = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"


def resolve_tts_config() -> dict[str, str]:
    model = (os.getenv("CARTESIA_MODEL") or DEFAULT_MODEL).strip()
    voice = (os.getenv("CARTESIA_VOICE_ID") or DEFAULT_VOICE_ID).strip()
    if model and "/" not in model:
        model = f"cartesia/{model}"
    return {"provider": "cartesia", "model": model, "voice": voice}


def build_tts():
    from livekit.agents import inference

    cfg = resolve_tts_config()
    api_key = os.getenv("CARTESIA_API_KEY", "").strip()
    if api_key:
        try:
            from livekit.plugins import cartesia
        except ImportError:
            cartesia = None
        if cartesia is not None:
            plugin_model = cfg["model"].removeprefix("cartesia/")
            return cartesia.TTS(model=plugin_model, voice=cfg["voice"], api_key=api_key)
    return inference.TTS(model=cfg["model"], voice=cfg["voice"])
