# EffiGov Agent

LiveKit resident voice worker. Talks to Effi-Backend to create, look up, and update cases.

Full local setup for all three services, including seeded Clerk logins, is in the workspace [instructions](https://github.com/markaschmidt/Effigov/blob/main/instructions.md).

## Run

```bash
cp .env.example .env.local
# fill LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
uv sync
uv run python -m services.agent console
# or, for the dashboard call booth:
uv run python -m services.agent dev
```

`EFFI_BACKEND_URL` defaults to `http://127.0.0.1:8000`.

The worker registers as `effi-gov-resident`. That name must match the backend token dispatch.

Cartesia is configured only in this worker. Put `CARTESIA_API_KEY` in `.env` or `.env.local` here, plus the same `EFFI_API_KEY` the backend expects.
