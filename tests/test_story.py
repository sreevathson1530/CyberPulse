"""The whole demo on Harish's simulated company: a quiet normal day, and an
account takeover caught before the damage starts."""

import pandas as pd
import pytest

from core.correlation import analyze, danger_over_time
from core.metrics import score_card
from core.schema import ACTIONS, COLUMNS, to_frame
from core.simulator import damage_start_time


def test_data_follows_the_agreed_format(normal_day, takeover):
    for events in (normal_day, takeover):
        assert list(events.columns[:len(COLUMNS)]) == COLUMNS
        assert set(events["action"]) <= set(ACTIONS)
        assert events["time"].is_monotonic_increasing
        assert events["event_id"].is_unique


def test_data_is_safe_to_show(normal_day, takeover):
    events = pd.concat([normal_day, takeover])
    assert events["ip"].str.startswith("203.0.113.").all()
    assert events["user"].str.endswith(".example").all()
    emails = events["target"][events["target"].str.contains("@")]
    assert emails.str.endswith(".example").all()


def test_unknown_actions_are_rejected():
    with pytest.raises(ValueError):
        to_frame([{"time": "2026-03-10 10:00", "user": "a@b.example", "ip": "203.0.113.10",
                   "device": "X", "country": "India", "action": "login_success"}])


def test_normal_day_raises_no_alarm(normal_day, profiles):
    incidents = analyze(normal_day, profiles)
    assert incidents, "the harmless oddities should still show up as Watch notes"
    assert all(incident.level == "Watch" for incident in incidents)


def test_takeover_is_one_red_incident(takeover, profiles):
    top = analyze(takeover, profiles)[0]
    assert top.kind == "Account takeover"
    assert top.level == "Likely attack"
    attack_ids = set(takeover.loc[takeover["label"] == "attack", "event_id"])
    assert attack_ids <= set(top.event_ids)


def test_meter_is_red_before_the_damage(takeover, profiles):
    damage = damage_start_time(takeover)
    before = takeover[takeover["time"] < damage]
    assert analyze(before, profiles)[0].level == "Likely attack"


def test_danger_only_climbs_during_the_attack(takeover, profiles):
    history = danger_over_time(takeover, profiles)
    assert history["score"].is_monotonic_increasing
    assert history["score"].iloc[-1] == 100


def test_score_card(normal_day, takeover, profiles):
    attack, normal = score_card(takeover, profiles), score_card(normal_day, profiles)
    assert attack["attacks_caught"] == attack["attack_events_total"] > 0
    assert attack["false_alarms"] == normal["false_alarms"] == 0
    assert attack["alarm_at"] < attack["red_at"] < damage_start_time(takeover)
    assert attack["minutes_of_warning"] >= 10
    assert normal["top_score"] < 40


def test_works_without_employee_profiles(takeover):
    assert analyze(takeover)[0].level == "Likely attack"
