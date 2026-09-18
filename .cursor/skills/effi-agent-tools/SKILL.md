---
name: effi-agent-tools
description: Backend tool contract for the EffiGov voice agent. Use when adding or changing function_tool methods that create, look up, or update cases.
---

# Agent tools

Tools live on `ResidentAgent` and must stay aligned with Effi-Backend schemas.

## When adding a tool

1. Add the HTTP method on `BackendClient` first
2. Decorate with `@function_tool()` and a docstring the LLM can follow (including `Args:`)
3. Confirm required slots in conversation before calling
4. Return a small JSON dict (`ok`, `case_number`, `status`) — never raw stack traces
5. Link the call with `_attach(case_id)` so the dashboard transcript lands on the case
6. Cover the client path with a test if the URL shape changed

Issue type values must be `missed_service | status_update | new_request | other`.
Status values must be `open | in_progress | waiting_on_resident | resolved`.
