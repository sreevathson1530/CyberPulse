"""Every incident gets a plain-English story."""

from core.correlation import ATTACK_KINDS, analyze
from core.explain import WHY_AND_WHAT_TO_DO, explain


def test_every_kind_has_an_explanation():
    assert set(WHY_AND_WHAT_TO_DO) == set(ATTACK_KINDS)


def test_every_incident_of_the_demo_explains(normal_day, takeover, profiles):
    for events in (normal_day, takeover):
        for incident in analyze(events, profiles):
            story = explain(incident)
            assert set(story) == {"title", "what_happened", "why_it_matters", "what_to_do"}
            assert all(text.strip() for text in story.values())


def test_takeover_story_names_the_person_and_the_intruder(takeover, profiles):
    story = explain(analyze(takeover, profiles)[0])
    assert story["title"] == "Account takeover · Likely attack"
    assert "Anita Rao" in story["what_happened"]
    assert "Romania" in story["what_happened"]
    assert "@" not in story["what_happened"]


def test_watch_level_says_it_is_low_risk(normal_day, profiles):
    incident = analyze(normal_day, profiles)[0]
    assert explain(incident)["why_it_matters"].startswith("On its own this is low risk.")
