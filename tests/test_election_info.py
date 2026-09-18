from __future__ import annotations

from services.election_info import TOPICS, election_facts


def test_election_facts_overview_includes_times_places_and_id() -> None:
    facts = election_facts("overview")
    assert facts["ok"] is True
    assert facts["topic"] == "overview"
    assert "November 3, 2026" in facts["election_date"]
    assert facts["poll_hours"].startswith("7:00 a.m.")
    assert len(facts["locations"]) == 3
    assert "state driver's license" in facts["documentation"]["photo_id"]


def test_election_facts_times_omits_locations() -> None:
    facts = election_facts("times")
    assert facts["topic"] == "times"
    assert "early_voting" in facts
    assert "locations" not in facts
    assert "documentation" not in facts


def test_election_facts_locations_use_cedarbrook_addresses() -> None:
    facts = election_facts("locations")
    addresses = {place["address"] for place in facts["locations"]}
    assert "100 Civic Plaza, Cedarbrook" in addresses
    assert "42 Marina Way, Cedarbrook" in addresses
    assert "880 Maple Street, Cedarbrook" in addresses


def test_election_facts_documentation_requires_photo_id() -> None:
    facts = election_facts("documentation")
    assert "U.S. passport" in facts["documentation"]["photo_id"]
    assert "60 days" in facts["documentation"]["proof_of_residency"]


def test_election_facts_unknown_topic_falls_back_to_overview() -> None:
    facts = election_facts("something else")
    assert facts["topic"] == "overview"
    assert facts["name"] == "Cedarbrook Municipal Election"


def test_known_topics_are_stable() -> None:
    assert TOPICS == {"overview", "times", "locations", "documentation"}
