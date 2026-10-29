"""Linking and scoring: turn warning signs into incidents.

Signs that share a person, IP address or device within 3 hours of each other
become one incident. Each incident gets a danger score from 0 to 100 and a
level: Watch, Suspicious or Likely attack.

`analyze()` is the whole backend in one call: events in, incidents out.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from core.detection import detect
from core.schema import OFFICE_IPS, to_frame

LINK_WINDOW = timedelta(hours=3)

SEVERITY_POINTS = {"Low": 5, "Medium": 15, "High": 25, "Critical": 40}
POINTS_PER_EXTRA_STAGE = 10
MAX_SCORE = 100

# Danger levels, highest first, each with the lowest score it starts at.
LEVELS = [(75, "Likely attack"), (40, "Suspicious"), (1, "Watch"), (0, "Clear")]

# Every kind attack_kind() can return. explain.py has text for each one.
ATTACK_KINDS = [
    "Ransomware",
    "Account takeover",
    "Email forwarding",
    "Data theft",
    "Unusual file activity",
    "Password guessing",
    "New admin",
    "Unusual login",
]


@dataclass
class Incident:
    """Warning signs linked into one story, with its danger score."""

    id: str        # e.g. "INC-001"
    signs: list    # WarningSign objects, oldest first
    score: int     # 0 to 100
    level: str     # "Watch", "Suspicious" or "Likely attack"
    kind: str      # one of ATTACK_KINDS

    @property
    def start(self):
        return self.signs[0].time

    @property
    def end(self):
        return self.signs[-1].time

    @property
    def users(self):
        return sorted({user for sign in self.signs for user in sign.users})

    @property
    def ips(self):
        return sorted({sign.ip for sign in self.signs})

    @property
    def devices(self):
        return sorted({sign.device for sign in self.signs})

    @property
    def steps(self):
        """The attack steps in the order they happened, each once."""
        return list(dict.fromkeys(sign.step for sign in self.signs))

    @property
    def event_ids(self):
        return list(dict.fromkeys(eid for sign in self.signs for eid in sign.event_ids))

    def timeline(self) -> pd.DataFrame:
        """One row per warning sign, oldest first, for the timeline chart."""
        return pd.DataFrame([{
            "time": sign.time,
            "step": sign.step,
            "severity": sign.severity,
            "users": ", ".join(sign.users),
            "ip": sign.ip,
            "device": sign.device,
            "country": sign.country,
            "detail": sign.detail,
        } for sign in self.signs])

    def evidence(self, events) -> pd.DataFrame:
        """The raw events behind this incident, for the evidence table."""
        events = to_frame(events)
        return events[events["event_id"].isin(set(self.event_ids))]


def analyze(events, employees=None, office_ips=OFFICE_IPS) -> list[Incident]:
    """Find, link and score everything in a log. Returns incidents, most
    dangerous first. During live playback, call it again with the events
    played so far."""
    signs = detect(events, employees, office_ips)
    incidents = []
    for number, group in enumerate(link(signs, office_ips), start=1):
        score = danger_score(group)
        incidents.append(Incident(f"INC-{number:03d}", group, score, danger_level(score), attack_kind(group)))
    return sorted(incidents, key=lambda incident: (-incident.score, incident.start))


def danger_over_time(events, employees=None, office_ips=OFFICE_IPS) -> pd.DataFrame:
    """The top danger score each time it changed: one row per moment a new
    warning sign appeared, with columns time, score and level.

    Rules and linking only look backwards, so the signs up to any moment are
    exactly the ones a live replay would have shown by then.
    """
    signs = sorted(detect(events, employees, office_ips), key=lambda sign: sign.time)
    rows = []
    for n, sign in enumerate(signs, start=1):
        if n < len(signs) and signs[n].time == sign.time:
            continue  # several signs at the same moment count once
        score = max(danger_score(group) for group in link(signs[:n], office_ips))
        if not rows or rows[-1]["score"] != score:
            rows.append({"time": sign.time, "score": score, "level": danger_level(score)})
    return pd.DataFrame(rows, columns=["time", "score", "level"])


def link(signs, office_ips=OFFICE_IPS, window=LINK_WINDOW) -> list[list]:
    """Group warning signs that share a person, IP address or device within
    `window` of each other. A chain counts: if A links to B and B to C, all
    three are one incident. The office's shared IP links nothing.

    Each group is a set in a union-find: parent[i] points towards the sign
    that stands for i's group, and two groups join by pointing one at the other.
    """
    signs = sorted(signs, key=lambda sign: sign.time)
    parent = list(range(len(signs)))

    def group_of(i):
        while parent[i] != i:
            i = parent[i]
        return i

    latest = {}  # ("ip", "203.0.113.50") -> index of the latest sign that had it
    for i, sign in enumerate(signs):
        for key in _link_keys(sign, office_ips):
            j = latest.get(key)
            if j is not None and sign.time - signs[j].time <= window:
                parent[group_of(j)] = group_of(i)
            latest[key] = i

    groups = defaultdict(list)
    for i, sign in enumerate(signs):
        groups[group_of(i)].append(sign)
    return sorted(groups.values(), key=lambda group: group[0].time)


def danger_score(signs) -> int:
    """Points for the most severe sign, plus 10 for each extra attack stage
    (each different rule that fired), up to 100."""
    if not signs:
        return 0
    highest = max(SEVERITY_POINTS[sign.severity] for sign in signs)
    stages = len({sign.rule for sign in signs})
    return min(MAX_SCORE, highest + POINTS_PER_EXTRA_STAGE * (stages - 1))


def danger_level(score) -> str:
    """1 to 39 is Watch, 40 to 74 Suspicious, 75 and up Likely attack."""
    for lowest, name in LEVELS:
        if score >= lowest:
            return name


def attack_kind(signs) -> str:
    """Name the kind of attack, so the matching explanation can be shown."""
    rules = {sign.rule for sign in signs}
    # A takeover needs a suspicious way in plus a second sign: both ways in,
    # or what the intruder did next. A forgotten password alone is not one.
    way_in = rules & {"login_after_failures", "new_device_or_country"}
    misuse = rules & {"external_forwarding", "made_admin", "mass_file_access", "big_upload"}
    if "mass_rename" in rules:
        return "Ransomware"
    if len(way_in) == 2 or (way_in and misuse):
        return "Account takeover"
    if "external_forwarding" in rules:
        return "Email forwarding"
    if "big_upload" in rules:
        return "Data theft"
    if "mass_file_access" in rules:
        return "Unusual file activity"
    if rules & {"brute_force", "password_spray", "login_after_failures"}:
        return "Password guessing"
    if "made_admin" in rules:
        return "New admin"
    return "Unusual login"


def _link_keys(sign, office_ips):
    keys = [("user", user) for user in sign.users]
    if sign.ip and sign.ip not in office_ips:
        keys.append(("ip", sign.ip))
    if sign.device:
        keys.append(("device", sign.device))
    return keys
