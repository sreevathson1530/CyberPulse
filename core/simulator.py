"""CyberPulse simulator: a fake company, a normal day, and an attack story.

Owner: Harish Karthick (data)

Everything here is invented and safe:
  * IP addresses come from 203.0.113.x (the reserved documentation range)
  * emails end in .example
  * a fixed random seed means every run gives exactly the same data

Every event carries a `label` ("normal" or "attack"), so we can later prove
how many attacks the app caught and how many false alarms it raised.

Quick use:
    from core.simulator import build_scenario
    normal = build_scenario("normal_day")
    attack = build_scenario("account_takeover")   # normal day + attack events

Command line (writes CSV files into data/scenarios/):
    python -m core.simulator
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
DAY = date(2026, 3, 10)  # a Tuesday
OFFICE_IP = "203.0.113.10"  # shared by everyone in the office (rules must ignore it)
ATTACKER_IP = "203.0.113.99"
ATTACKER_DEVICE = "UNKNOWN-DEV-7731"
ATTACKER_COUNTRY = "Romania"
FORWARD_ADDRESS = "anita.backup@mailbox-forward.example"

# One log event = one row with exactly these columns. Keep in sync with core/schema.py.
COLUMNS = [
    "event_id",   # E0001, E0002 ... in time order
    "timestamp",  # datetime
    "user",       # employee email
    "ip",         # source IP address
    "device",     # device name
    "country",    # country of the login or action
    "action",     # see ACTIONS below
    "detail",     # free text, e.g. file name or forwarding address
    "label",      # "normal" or "attack"   (answer key, the backend must NOT use it)
    "stage",      # attack step name, empty for normal events
    "note",       # why a normal event looks odd, empty otherwise
]

ACTIONS = [
    "login_success",
    "login_failed",
    "logout",
    "file_open",
    "email_sent",
    "admin_granted",
    "mail_rule_created",
]


# --------------------------------------------------------------------------
# The fake company
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Employee:
    name: str
    team: str
    email: str
    device: str
    country: str
    ip: str          # where they usually log in from
    start_hour: float  # usual start of the working day (24h clock)
    end_hour: float


def _email(first: str, last: str) -> str:
    return f"{first.lower()}.{last.lower()}@cyberpulse.example"


EMPLOYEES = [
    Employee("Anita Rao",     "Finance",     _email("anita", "rao"),     "LAPTOP-ANITA",  "India", OFFICE_IP,      9.0, 17.5),
    Employee("Ravi Menon",    "Sales",       _email("ravi", "menon"),    "LAPTOP-RAVI",   "India", "203.0.113.21", 9.5, 18.0),
    Employee("Divya Nair",    "HR",          _email("divya", "nair"),    "LAPTOP-DIVYA",  "India", OFFICE_IP,      9.0, 17.0),
    Employee("Karthik Iyer",  "Engineering", _email("karthik", "iyer"),  "LAPTOP-KARTHIK", "India", OFFICE_IP,     10.0, 18.5),
    Employee("Sana Khan",     "Engineering", _email("sana", "khan"),     "LAPTOP-SANA",   "India", OFFICE_IP,     10.0, 18.5),
    Employee("Mohan Das",     "IT Admin",    _email("mohan", "das"),     "LAPTOP-MOHAN",  "India", OFFICE_IP,      8.5, 17.0),
    Employee("Priya Sharma",  "Marketing",   _email("priya", "sharma"),  "LAPTOP-PRIYA",  "India", "203.0.113.34", 9.5, 18.0),
    Employee("Arjun Patel",   "Operations",  _email("arjun", "patel"),   "LAPTOP-ARJUN",  "India", OFFICE_IP,      9.0, 17.5),
]
BY_NAME = {e.name.split()[0].lower(): e for e in EMPLOYEES}

FILE_NAMES = {
    "Finance":     ["invoice_{n}.pdf", "ledger_{n}.xlsx", "payroll_{n}.xlsx", "budget_{n}.xlsx"],
    "Sales":       ["lead_list_{n}.xlsx", "proposal_{n}.docx", "quote_{n}.pdf"],
    "HR":          ["leave_form_{n}.pdf", "review_{n}.docx", "offer_letter_{n}.docx"],
    "Engineering": ["design_{n}.md", "report_{n}.pdf", "spec_{n}.docx"],
    "IT Admin":    ["access_list_{n}.csv", "patch_notes_{n}.txt", "inventory_{n}.xlsx"],
    "Marketing":   ["campaign_{n}.pptx", "brand_{n}.pdf", "post_{n}.docx"],
    "Operations":  ["shipment_{n}.xlsx", "stock_{n}.csv", "schedule_{n}.docx"],
}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def _at(hour: float) -> datetime:
    """A datetime on DAY at a decimal hour, e.g. 13.75 -> 13:45."""
    return datetime.combine(DAY, datetime.min.time()) + timedelta(hours=hour)


def _event(ts, emp_or_user, action, *, ip=None, device=None, country=None,
           detail="", label="normal", stage="", note="") -> dict:
    """Build one event row. `emp_or_user` is an Employee or a plain email."""
    if isinstance(emp_or_user, Employee):
        user = emp_or_user.email
        ip = ip or emp_or_user.ip
        device = device or emp_or_user.device
        country = country or emp_or_user.country
    else:
        user = emp_or_user
    return {
        "event_id": "",
        "timestamp": ts,
        "user": user,
        "ip": ip,
        "device": device,
        "country": country,
        "action": action,
        "detail": detail,
        "label": label,
        "stage": stage,
        "note": note,
    }


def _random_file(rng: random.Random, emp: Employee) -> str:
    return rng.choice(FILE_NAMES[emp.team]).format(n=rng.randint(1, 400))


# --------------------------------------------------------------------------
# A normal day (about 2,000 events)
# --------------------------------------------------------------------------
def _normal_events(rng: random.Random) -> list[dict]:
    events: list[dict] = []
    for emp in EMPLOYEES:
        login_at = _at(emp.start_hour + rng.uniform(-0.25, 0.4))
        logout_at = _at(emp.end_hour + rng.uniform(-0.3, 0.3))
        events.append(_event(login_at, emp, "login_success"))

        work_start, work_end = login_at + timedelta(minutes=3), logout_at
        span = (work_end - work_start).total_seconds()

        for _ in range(rng.randint(170, 220)):
            ts = work_start + timedelta(seconds=rng.uniform(0, span))
            events.append(_event(ts, emp, "file_open", detail=_random_file(rng, emp)))
        for _ in range(rng.randint(35, 55)):
            ts = work_start + timedelta(seconds=rng.uniform(0, span))
            recipient = rng.choice(EMPLOYEES).email
            events.append(_event(ts, emp, "email_sent", detail=f"to {recipient}"))

        events.append(_event(logout_at, emp, "logout"))
    return events


# --------------------------------------------------------------------------
# Harmless odd things (these must NOT turn red; they are the false-alarm test)
# --------------------------------------------------------------------------
def _harmless_odd_events(rng: random.Random) -> list[dict]:
    events: list[dict] = []
    ravi, priya, mohan = BY_NAME["ravi"], BY_NAME["priya"], BY_NAME["mohan"]
    sana, divya, arjun, anita = BY_NAME["sana"], BY_NAME["divya"], BY_NAME["arjun"], BY_NAME["anita"]
    karthik = BY_NAME["karthik"]

    # 1. Someone travelling: Priya logs in from Singapore on her usual laptop.
    events.append(_event(_at(11.2), priya, "login_success", ip="203.0.113.150",
                         country="Singapore",
                         note="harmless: Priya is travelling for a conference"))

    # 2. Forgotten password: Ravi fails 3 times, then gets in.
    for i, minute in enumerate([0, 1, 2]):
        events.append(_event(_at(9.9) + timedelta(minutes=minute), ravi, "login_failed",
                             detail="wrong password",
                             note="harmless: Ravi forgot his password"))
    events.append(_event(_at(9.9) + timedelta(minutes=4), ravi, "login_success",
                         note="harmless: Ravi forgot his password"))

    # 3. IT admin gives rights during work hours, with a ticket.
    events.append(_event(_at(11.5), mohan, "admin_granted",
                         detail=f"granted admin to {karthik.email}, IT ticket #4821",
                         note="harmless: planned change by the IT admin"))

    # 4. Late evening login from the usual laptop.
    events.append(_event(_at(21.4), divya, "login_success",
                         note="harmless: Divya finishing a late task"))
    for _ in range(6):
        events.append(_event(_at(21.45) + timedelta(minutes=rng.randint(0, 20)),
                             divya, "file_open", detail=_random_file(rng, divya),
                             note="harmless: Divya finishing a late task"))
    events.append(_event(_at(21.9), divya, "logout",
                         note="harmless: Divya finishing a late task"))

    # 5. New laptop for Sana (new device, same person, same office).
    events.append(_event(_at(10.3), sana, "login_success", device="LAPTOP-SANA-NEW",
                         note="harmless: Sana received a replacement laptop"))

    # 6. Month-end rush: Arjun opens 60 extra files in half an hour.
    for _ in range(60):
        ts = _at(15.0) + timedelta(seconds=rng.uniform(0, 30 * 60))
        events.append(_event(ts, arjun, "file_open", detail=_random_file(rng, arjun),
                             note="harmless: month-end stock report"))

    # 7. Anita mistypes her password twice (not 5).
    for minute in (0, 1):
        events.append(_event(_at(9.4) + timedelta(minutes=minute), anita, "login_failed",
                             detail="wrong password",
                             note="harmless: Anita mistyped her password"))
    return events


# --------------------------------------------------------------------------
# Attack story 1: account takeover of Anita Rao (Finance)
# --------------------------------------------------------------------------
def _account_takeover_events(rng: random.Random) -> list[dict]:
    anita = BY_NAME["anita"]
    atk = dict(ip=ATTACKER_IP, label="attack")
    events: list[dict] = []

    # Stage 1: password spraying, one IP tries 4 other accounts (rule: 4+ accounts).
    t = _at(13.67)  # 13:40
    for name in ("ravi", "divya", "karthik", "sana"):
        victim = BY_NAME[name]
        events.append(_event(t, victim.email, "login_failed", device=ATTACKER_DEVICE,
                             country=ATTACKER_COUNTRY, detail="wrong password",
                             stage="password_spray", **atk))
        t += timedelta(seconds=rng.randint(40, 70))

    # Stage 2: password guessing on Anita, 6 failures in 7 minutes (rule: 5 in 10 min).
    t = _at(13.75)  # 13:45
    for _ in range(6):
        events.append(_event(t, anita.email, "login_failed", device=ATTACKER_DEVICE,
                             country=ATTACKER_COUNTRY, detail="wrong password",
                             stage="password_guessing", **atk))
        t += timedelta(seconds=rng.randint(55, 80))

    # Stage 3: the guess works, from a device and country she has never used.
    events.append(_event(_at(13.88), anita.email, "login_success", device=ATTACKER_DEVICE,
                         country=ATTACKER_COUNTRY, stage="new_device_login", **atk))

    # Stage 4: hidden mail-forwarding rule to an outside address.
    events.append(_event(_at(13.97), anita.email, "mail_rule_created", device=ATTACKER_DEVICE,
                         country=ATTACKER_COUNTRY,
                         detail=f"forward all mail to {FORWARD_ADDRESS}",
                         stage="mail_forwarding_rule", **atk))

    # Stage 5: the account makes itself admin.
    events.append(_event(_at(14.05), anita.email, "admin_granted", device=ATTACKER_DEVICE,
                         country=ATTACKER_COUNTRY,
                         detail=f"self-granted admin to {anita.email}",
                         stage="made_admin", **atk))

    # Stage 6: mass file opening, 150 files in 10 minutes. This is the damage.
    start = _at(14.13)  # 14:08
    for i in range(150):
        ts = start + timedelta(seconds=i * 4 + rng.uniform(0, 2))
        events.append(_event(ts, anita.email, "file_open", device=ATTACKER_DEVICE,
                             country=ATTACKER_COUNTRY,
                             detail=_random_file(rng, anita), stage="mass_download", **atk))
    return events


# --------------------------------------------------------------------------
# Putting it together
# --------------------------------------------------------------------------
SCENARIOS = ["normal_day", "account_takeover"]


def build_scenario(name: str = "normal_day") -> pd.DataFrame:
    """Return all events of a scenario as a time-sorted DataFrame with COLUMNS."""
    if name not in SCENARIOS:
        raise ValueError(f"Unknown scenario {name!r}. Choose from {SCENARIOS}")

    rng = random.Random(SEED)  # same seed every call = same data every time
    events = _normal_events(rng) + _harmless_odd_events(rng)
    if name == "account_takeover":
        events += _account_takeover_events(rng)

    df = pd.DataFrame(events, columns=COLUMNS)
    df = df.sort_values("timestamp", kind="stable").reset_index(drop=True)
    df["event_id"] = [f"E{i:04d}" for i in range(1, len(df) + 1)]
    return df


def damage_start_time(df: pd.DataFrame):
    """When the real damage begins (first mass download). None for a normal day."""
    hit = df[df["stage"] == "mass_download"]
    return None if hit.empty else hit["timestamp"].min()


# --------------------------------------------------------------------------
# Day-one gift for Sreevathson: ready-made warnings to test linking
# --------------------------------------------------------------------------
def sample_warnings(df: pd.DataFrame) -> list[dict]:
    """Warnings roughly as the six rules would produce them, for the takeover story.

    Each warning: id, rule, severity, user, ip, device, timestamp, event_ids,
    plus `is_attack` (answer key) so linking tests can check the outcome.
    """
    def ids(stage):
        return df.loc[df["stage"] == stage, "event_id"].tolist()

    def first(stage):
        return df[df["stage"] == stage].iloc[0]

    anita = BY_NAME["anita"].email
    guess, spray = first("password_guessing"), first("password_spray")
    login, admin = first("new_device_login"), first("made_admin")
    files = df[df["stage"] == "mass_download"]
    priya_trip = df[df["note"].str.contains("travelling", na=False)].iloc[0]

    def w(n, rule, severity, row, event_ids, is_attack=True, **over):
        base = {
            "warning_id": f"W{n:03d}", "rule": rule, "severity": severity,
            "user": row["user"], "ip": row["ip"], "device": row["device"],
            "timestamp": row["timestamp"].isoformat(), "event_ids": event_ids,
            "is_attack": is_attack,
        }
        base.update(over)
        return base

    return [
        w(1, "one_ip_many_accounts", "Medium", spray, ids("password_spray"), user=None),
        w(2, "too_many_failed_logins", "High", guess, ids("password_guessing")),
        w(3, "login_after_failures", "High", login, ids("new_device_login")),
        w(4, "new_device_or_country", "Medium", login, ids("new_device_login")),
        w(5, "sudden_admin", "Critical", admin, ids("made_admin")),
        w(6, "unusual_file_volume", "High", files.iloc[-1], files["event_id"].tolist()),
        # A harmless decoy: linking must not tie this to the attack.
        w(7, "new_device_or_country", "Medium", priya_trip, [priya_trip["event_id"]],
          is_attack=False),
    ]


# --------------------------------------------------------------------------
# Run this file to (re)write the data files
# --------------------------------------------------------------------------
def write_all(out_dir: str | Path = "data/scenarios") -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for name in SCENARIOS:
        df = build_scenario(name)
        df.to_csv(out / f"{name}.csv", index=False)
        print(f"{name}: {len(df)} events, {(df['label'] == 'attack').sum()} attack events")
    attack_df = build_scenario("account_takeover")
    (out / "sample_warnings.json").write_text(
        json.dumps(sample_warnings(attack_df), indent=2), encoding="utf-8"
    )
    print("sample_warnings.json written")


if __name__ == "__main__":
    write_all()
