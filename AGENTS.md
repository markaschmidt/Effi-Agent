# Effi-Agent

LiveKit Agents project. Use `uv run python -m services.agent` as the only entrypoint.

Keep tool docstrings precise. Confirm resident details before calling `create_case`. Stream transcripts to the backend; complete the call on shutdown.

Build TTS through `src/services/cartesia.py` from `CARTESIA_*` env only. Send `EFFI_API_KEY` when calling Effi-Backend.

If LiveKit docs are needed, use `lk docs` or the LiveKit docs MCP. Do not guess new Agents APIs.
