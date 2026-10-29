"""Score card numbers for CyberPulse.

Owner: Harish Karthick (data)

Feed in the events and the set of event_ids the backend flagged as suspicious.
You get the three numbers Aswin shows on the score card:
  * attacks caught
  * false alarms
  * minutes of warning before the damage starts
"""

from __future__ import annotations

import pandas as pd


def compute_metrics(events: pd.DataFrame, flagged_event_ids) -> dict:
    """Compare what the backend flagged with the answer key (the `label` column).

    events            DataFrame from core.simulator.build_scenario()
    flagged_event_ids any collection of event_ids the detection rules flagged
    """
    flagged = set(flagged_event_ids)
    is_attack = events["label"] == "attack"
    is_flagged = events["event_id"].isin(flagged)

    attack_total = int(is_attack.sum())
    attacks_caught = int((is_attack & is_flagged).sum())
    false_alarms = int((~is_attack & is_flagged).sum())

    # Minutes of warning: first flagged attack event -> start of the damage.
    minutes_of_warning = None
    damage = events.loc[events["stage"] == "mass_download", "timestamp"]
    caught = events.loc[is_attack & is_flagged, "timestamp"]
    if not damage.empty and not caught.empty:
        gap = (damage.min() - caught.min()).total_seconds() / 60
        minutes_of_warning = round(max(gap, 0.0), 1)

    return {
        "attack_events_total": attack_total,
        "attacks_caught": attacks_caught,
        "detection_rate": round(attacks_caught / attack_total, 3) if attack_total else None,
        "false_alarms": false_alarms,
        "minutes_of_warning": minutes_of_warning,
    }
