"""Score card numbers for CyberPulse.

Owner: Harish Karthick (data)

Feed in the events and the set of event_ids the backend flagged as suspicious.
You get the three numbers Aswin shows on the score card:
  * attacks caught
  * false alarms
  * minutes of warning before the damage starts

`score_card()` does the whole job: it runs the backend over a scenario and
scores the result against the answer key.
"""

from __future__ import annotations

import pandas as pd

from core.correlation import analyze, danger_over_time
from core.schema import to_frame

# An incident at one of these levels is an alarm: someone should act on it.
# Watch-level incidents are notes, not alarms.
ALARM_LEVELS = ("Suspicious", "Likely attack")


def compute_metrics(events: pd.DataFrame, flagged_event_ids, alert_time=None) -> dict:
    """Compare what the backend flagged with the answer key (the `label` column).

    events            DataFrame from core.simulator.build_scenario()
    flagged_event_ids any collection of event_ids the detection rules flagged
    alert_time        when the alarm went off; without it, the time of the
                      first flagged attack event is used
    """
    flagged = set(flagged_event_ids)
    is_attack = events["label"] == "attack"
    is_flagged = events["event_id"].isin(flagged)

    attack_total = int(is_attack.sum())
    attacks_caught = int((is_attack & is_flagged).sum())
    false_alarms = int((~is_attack & is_flagged).sum())

    # Minutes of warning: the alarm (or first flagged attack event) -> start of the damage.
    minutes_of_warning = None
    damage = events.loc[events["stage"] == "mass_download", "time"]
    caught = events.loc[is_attack & is_flagged, "time"]
    warned_at = alert_time if alert_time is not None else (caught.min() if not caught.empty else None)
    if not damage.empty and warned_at is not None:
        gap = (damage.min() - warned_at).total_seconds() / 60
        minutes_of_warning = round(max(gap, 0.0), 1)

    return {
        "attack_events_total": attack_total,
        "attacks_caught": attacks_caught,
        "detection_rate": round(attacks_caught / attack_total, 3) if attack_total else None,
        "false_alarms": false_alarms,
        "minutes_of_warning": minutes_of_warning,
    }


def score_card(events, employees=None) -> dict:
    """Run the backend over a scenario and score it against the answer key.

    Adds to compute_metrics(): the top danger score, when the first alarm went
    off (alarm_at) and when the meter turned red (red_at), and how many minutes
    before the damage it turned red.
    """
    events = to_frame(events)
    incidents = analyze(events, employees)
    flagged = {eid for incident in incidents if incident.level in ALARM_LEVELS for eid in incident.event_ids}

    history = danger_over_time(events, employees)
    alarms = history[history["level"].isin(ALARM_LEVELS)]
    red = history[history["level"] == "Likely attack"]
    alarm_at = alarms["time"].min() if not alarms.empty else None
    red_at = red["time"].min() if not red.empty else None

    result = compute_metrics(events, flagged, alarm_at)
    red_minutes = compute_metrics(events, flagged, red_at)["minutes_of_warning"] if red_at is not None else None
    result.update({
        "top_score": max((incident.score for incident in incidents), default=0),
        "incidents": len(incidents),
        "alarm_at": alarm_at,
        "red_at": red_at,
        "minutes_red_before_damage": red_minutes,
    })
    return result
