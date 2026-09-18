from __future__ import annotations

import asyncio
import json
import logging
import os
import textwrap
from typing import Any

from dotenv import load_dotenv
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    ConversationItemAddedEvent,
    JobContext,
    RunContext,
    TurnHandlingOptions,
    UserInputTranscribedEvent,
    cli,
    function_tool,
    inference,
    room_io,
)

from backend import BackendClient, backend_api_key
from services.cartesia import build_tts
from services.election_info import election_facts

logger = logging.getLogger("effi-agent")

load_dotenv(".env.local")
load_dotenv(".env")

BACKEND_URL = os.getenv("EFFI_BACKEND_URL", "http://127.0.0.1:8000")
try:
    from livekit.plugins import ai_coustics
except ImportError:
    ai_coustics = None

INSTRUCTIONS = textwrap.dedent(
    """\
    You are Effi, the EffiGov resident services voice agent for Cedarbrook.

    You are speaking on a phone call. Keep replies to one or two short sentences. Ask only one question at a time.

    Many callers only want information. Do not create a case, collect a name, or collect a phone number unless they are reporting a missed city service, filing a new request, or asking you to look up or update an existing case.

    For questions about the Cedarbrook municipal election, call get_election_info. Answer from the tool result: election day and hours, early voting, polling places, and what photo ID or proof of residency to bring. Do not invent extra election rules. If they only want election information, never open a case.

    If they do want a service case, collect, in this order, before you create a new case:
    1. Full name
    2. Phone number
    3. Whether they are reporting a missed service, checking an existing case, or making a new request
    4. A short description of the issue

    If they want an update, look up the case by phone number or case number such as E G one zero zero one.
    Confirm the details out loud before you create or update a case, then use a tool.
    After a case tool succeeds, tell them the case number slowly, digit by digit, and the current status.
    Never invent a case number. If a tool fails, say you could not save it and offer to try again.

    Speak plainly. No lists, markdown, or acronyms unless the resident used them first.
    """
)


class ResidentAgent(Agent):
    def __init__(self, client: BackendClient, call_id: str) -> None:
        super().__init__(
            llm=inference.LLM(model="google/gemma-4-31b-it"),
            instructions=INSTRUCTIONS,
        )
        self._client = client
        self._call_id = call_id
        self._active_case_id: str | None = None

    @function_tool()
    async def get_election_info(
        self,
        context: RunContext,
        topic: str = "overview",
    ) -> dict[str, Any]:
        """Look up Cedarbrook municipal election times, polling places, or ID rules. Use this for information-only questions. Do not create a case.

        Args:
            topic: One of overview, times, locations, or documentation.
        """
        return election_facts(topic)

    async def _attach(self, case_id: str) -> None:
        self._active_case_id = case_id
        await self._client.link_call(self._call_id, case_id)

    @function_tool()
    async def create_case(
        self,
        context: RunContext,
        resident_name: str,
        phone_number: str,
        issue_type: str,
        description: str,
    ) -> dict[str, Any]:
        """Create a new resident case after confirming the details.

        Args:
            resident_name: Resident full name.
            phone_number: Callback number, digits spoken by the resident.
            issue_type: One of missed_service, status_update, new_request, or other.
            description: Short description of the request in the resident's words.
        """
        allowed = {"missed_service", "status_update", "new_request", "other"}
        normalized = issue_type.strip().lower().replace(" ", "_")
        if normalized not in allowed:
            normalized = "other"
        case = await self._client.create_case(
            resident_name=resident_name,
            phone_number=phone_number,
            issue_type=normalized,
            description=description,
            call_id=self._call_id,
        )
        await self._attach(case["id"])
        logger.info("Created case %s", case["case_number"])
        return {
            "ok": True,
            "case_number": case["case_number"],
            "status": case["status"],
            "issue_type": case["issue_type"],
        }

    @function_tool()
    async def lookup_case(
        self,
        context: RunContext,
        phone_number: str = "",
        case_number: str = "",
    ) -> dict[str, Any]:
        """Look up an existing case by phone number or case number.

        Args:
            phone_number: Resident phone number if they do not know the case number.
            case_number: Case number like EG-1001 if they have it.
        """
        if case_number:
            try:
                case = await self._client.get_case(case_number.upper())
            except Exception:
                return {"ok": False, "reason": "No case found for that case number."}
            await self._attach(case["id"])
            return {
                "ok": True,
                "case_number": case["case_number"],
                "resident_name": case["resident_name"],
                "status": case["status"],
                "issue_type": case["issue_type"],
                "description": case["description"],
                "notes": case["notes"],
            }
        if not phone_number:
            return {"ok": False, "reason": "Need a phone number or case number."}
        matches = await self._client.lookup_phone(phone_number)
        if not matches:
            return {"ok": False, "reason": "No cases found for that phone number."}
        case = matches[0]
        await self._attach(case["id"])
        return {
            "ok": True,
            "matches": len(matches),
            "case_number": case["case_number"],
            "resident_name": case["resident_name"],
            "status": case["status"],
            "issue_type": case["issue_type"],
            "description": case["description"],
        }

    @function_tool()
    async def update_case(
        self,
        context: RunContext,
        case_number: str,
        status: str = "",
        notes: str = "",
        description: str = "",
    ) -> dict[str, Any]:
        """Update an existing case after looking it up.

        Args:
            case_number: Case number to update, like EG-1001.
            status: Optional new status: open, in_progress, waiting_on_resident, or resolved.
            notes: Optional note to append for staff.
            description: Optional replacement description.
        """
        fields: dict[str, Any] = {}
        if status:
            fields["status"] = status
        if notes:
            fields["notes"] = notes
        if description:
            fields["description"] = description
        if not fields:
            return {"ok": False, "reason": "Nothing to update."}
        case = await self._client.update_case(case_number.upper(), **fields)
        await self._attach(case["id"])
        return {
            "ok": True,
            "case_number": case["case_number"],
            "status": case["status"],
            "notes": case["notes"],
        }


server = AgentServer()


def _job_metadata(ctx: JobContext) -> dict[str, Any]:
    raw = ctx.job.metadata or ""
    if not raw:
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


@server.rtc_session(agent_name="effi-gov-resident")
async def resident_session(ctx: JobContext) -> None:
    ctx.log_context_fields = {"room": ctx.room.name}
    client = BackendClient(BACKEND_URL, api_key=backend_api_key())
    meta = _job_metadata(ctx)
    call = await client.get_or_create_call(ctx.room.name, case_id=meta.get("case_id"))
    call_id = meta.get("call_id") or call["id"]
    logger.info("Attached to call %s in room %s", call_id, ctx.room.name)

    session = AgentSession(
        stt=inference.STT(model="deepgram/nova-3", language="en"),
        tts=build_tts(),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
            interruption={"mode": "adaptive"},
            preemptive_generation={"enabled": True},
        ),
    )

    async def post_transcript(role: str, text: str, is_final: bool = True) -> None:
        try:
            await client.post_transcript(call_id, role, text, is_final=is_final)
        except Exception:
            logger.warning("Could not persist %s transcript for call %s", role, call_id)

    @session.on("user_input_transcribed")
    def on_user_input(event: UserInputTranscribedEvent) -> None:
        if not event.transcript.strip():
            return
        asyncio.create_task(post_transcript("resident", event.transcript, is_final=event.is_final))

    @session.on("conversation_item_added")
    def on_item(event: ConversationItemAddedEvent) -> None:
        item = event.item
        role = getattr(item, "role", "")
        text = (getattr(item, "text_content", None) or "").strip()
        if role == "assistant" and text:
            asyncio.create_task(post_transcript("agent", text))

    async def shutdown() -> None:
        recorder = getattr(session, "_recorder_io", None)
        if recorder is not None:
            try:
                await recorder.aclose()
            except Exception:
                logger.exception("Failed to close call recorder")
        audio_path = ctx.session_directory / "audio.ogg"
        if audio_path.is_file() and audio_path.stat().st_size > 0:
            try:
                await client.upload_recording(call_id, audio_path)
            except Exception:
                logger.exception("Failed to upload recording for call %s", call_id)
        try:
            await client.complete_call(call_id)
        except Exception:
            logger.exception("Failed to complete call %s", call_id)
        await client.aclose()

    room_options = room_io.RoomOptions()
    if ai_coustics is not None:
        room_options = room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_S
                )
            )
        )

    await session.start(
        agent=ResidentAgent(client, call_id),
        room=ctx.room,
        room_options=room_options,
        record={"audio": True},
    )
    ctx.add_shutdown_callback(shutdown)
    await ctx.connect()
    await session.generate_reply(
        instructions=(
            "Greet the resident, say you are Effi with Cedarbrook resident services, "
            "and ask how you can help with city services or election information."
        )
    )


if __name__ == "__main__":
    cli.run_app(server)
