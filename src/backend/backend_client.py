from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx


class BackendClient:
    """Thin async client for Effi-Backend case and call endpoints."""

    def __init__(self, base_url: str, api_key: str = "") -> None:
        headers = {"X-API-Key": api_key} if api_key else {}
        self._http = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=60.0, headers=headers)

    async def aclose(self) -> None:
        await self._http.aclose()

    async def get_or_create_call(self, room_name: str, case_id: str | None = None) -> dict[str, Any]:
        response = await self._http.post("/calls", json={"room_name": room_name, "case_id": case_id})
        response.raise_for_status()
        return response.json()

    async def link_call(self, call_id: str, case_id: str) -> dict[str, Any]:
        response = await self._http.post(f"/calls/{call_id}/link", json={"case_id": case_id})
        response.raise_for_status()
        return response.json()

    async def create_case(
        self,
        *,
        resident_name: str,
        phone_number: str,
        issue_type: str,
        description: str,
        call_id: str | None = None,
    ) -> dict[str, Any]:
        response = await self._http.post(
            "/cases",
            json={
                "resident_name": resident_name,
                "phone_number": phone_number,
                "issue_type": issue_type,
                "description": description,
                "source": "voice_agent",
                "call_id": call_id,
            },
        )
        response.raise_for_status()
        return response.json()

    async def lookup_phone(self, phone_number: str) -> list[dict[str, Any]]:
        response = await self._http.get(f"/lookups/phone/{phone_number}")
        response.raise_for_status()
        return response.json()

    async def get_case(self, case_id: str) -> dict[str, Any]:
        response = await self._http.get(f"/cases/{case_id}")
        response.raise_for_status()
        return response.json()

    async def update_case(self, case_id: str, **fields: Any) -> dict[str, Any]:
        payload = {key: value for key, value in fields.items() if value is not None}
        payload["source"] = "voice_agent"
        response = await self._http.patch(f"/cases/{case_id}", json=payload)
        response.raise_for_status()
        return response.json()

    async def post_transcript(
        self,
        call_id: str,
        role: str,
        text: str,
        is_final: bool = True,
    ) -> None:
        response = await self._http.post(
            f"/calls/{call_id}/transcript",
            json={"role": role, "text": text, "is_final": is_final},
        )
        response.raise_for_status()

    async def complete_call(self, call_id: str) -> dict[str, Any]:
        response = await self._http.post(f"/calls/{call_id}/complete")
        response.raise_for_status()
        return response.json()

    async def upload_recording(self, call_id: str, path: str | Path, content_type: str = "audio/ogg") -> dict[str, Any]:
        audio_path = Path(path)
        files = {"file": (audio_path.name, audio_path.read_bytes(), content_type)}
        response = await self._http.post(f"/calls/{call_id}/recordings", files=files)
        response.raise_for_status()
        return response.json()


def backend_api_key() -> str:
    return os.getenv("EFFI_API_KEY", "").strip()
