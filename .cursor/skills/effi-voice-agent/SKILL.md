---
name: effi-voice-agent
description: EffiGov LiveKit resident voice agent. Use when changing greetings, tools, STT/LLM/TTS, transcript hooks, or backend calls from Effi-Agent.
---

# Effi voice agent

Entrypoint: `src/services/agent.py` (`uv run python -m services.agent`). Worker name: `effi-gov-resident`.

```bash
uv run python -m services.agent console   # terminal mic
uv run python -m services.agent dev       # LiveKit Cloud rooms
```

## Tools

`create_case`, `lookup_case`, `update_case` in `ResidentAgent`. They call `BackendClient`. Do not invent case numbers in instructions.

## Session wiring

On job start: `get_or_create_call(room_name)` using dispatch metadata `call_id` when present.
On `user_input_transcribed` / assistant `conversation_item_added`: POST transcript (interim frames use `is_final=false`).
On shutdown: `complete_call` so analysis can fill summary.

## Voice stack

Voice AI stays in this repo. LiveKit inference: Deepgram Nova 3, Gemma 4 31B, Cartesia Sonic 3. TTS is built in `src/services/cartesia.py` from `CARTESIA_*` env (the key lives in Effi-Agent `.env`, not the backend). If `CARTESIA_API_KEY` is set, use `livekit-plugins-cartesia`; otherwise `inference.TTS`. Send `EFFI_API_KEY` on every BackendClient call. Keep replies one to two sentences. Ask one question at a time.

If `livekit-plugins-ai-coustics` is missing, skip noise cancellation rather than failing startup.
