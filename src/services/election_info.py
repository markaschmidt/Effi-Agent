"""Fictitious Cedarbrook municipal election facts for information-only calls."""

from __future__ import annotations

from typing import Any

TOPICS = frozenset({"overview", "times", "locations", "documentation"})

ELECTION = {
    "city": "Cedarbrook",
    "name": "Cedarbrook Municipal Election",
    "election_date": "Tuesday, November 3, 2026",
    "poll_hours": "7:00 a.m. to 8:00 p.m.",
    "early_voting": (
        "Monday, October 19 through Sunday, November 1, 2026, "
        "9:00 a.m. to 6:00 p.m. at Cedarbrook City Hall only"
    ),
    "locations": [
        {
            "name": "Cedarbrook City Hall",
            "address": "100 Civic Plaza, Cedarbrook",
            "notes": "Election Day polling place and the only early-voting site",
        },
        {
            "name": "Harborview Community Center",
            "address": "42 Marina Way, Cedarbrook",
            "notes": "Election Day polling place; ballot drop box in the lobby",
        },
        {
            "name": "Northridge Public Library",
            "address": "880 Maple Street, Cedarbrook",
            "notes": "Election Day polling place; ballot drop box by the main entrance",
        },
    ],
    "documentation": {
        "photo_id": [
            "state driver's license",
            "state ID card",
            "U.S. passport",
            "military ID",
            "city employee badge",
        ],
        "proof_of_residency": (
            "If the address on the photo ID is outdated, also bring a utility bill, "
            "lease, or bank statement dated within the last 60 days."
        ),
        "first_time_mail_registrants": (
            "First-time voters who registered by mail should also bring the voter "
            "ID card mailed by the city clerk."
        ),
    },
}


def election_facts(topic: str = "overview") -> dict[str, Any]:
    """Return a small JSON payload the voice agent can speak from.

    Unknown topics fall back to overview so the model never gets an empty result.
    """
    normalized = (topic or "overview").strip().lower().replace(" ", "_")
    if normalized not in TOPICS:
        normalized = "overview"

    payload: dict[str, Any] = {
        "ok": True,
        "topic": normalized,
        "city": ELECTION["city"],
        "name": ELECTION["name"],
        "election_date": ELECTION["election_date"],
    }
    if normalized in {"overview", "times"}:
        payload["poll_hours"] = ELECTION["poll_hours"]
        payload["early_voting"] = ELECTION["early_voting"]
    if normalized in {"overview", "locations"}:
        payload["locations"] = ELECTION["locations"]
    if normalized in {"overview", "documentation"}:
        payload["documentation"] = ELECTION["documentation"]
    return payload
