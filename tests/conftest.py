"""Shared test helpers: a small fake company and a quick way to write events.

Owner: Keerthana (testing). Run every test with:  python -m pytest
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.schema import Employee, to_frame  # noqa: E402
from core.simulator import build_scenario, employee_profiles  # noqa: E402

OFFICE = "203.0.113.10"
ATTACKER = "203.0.113.66"
DAY = datetime(2026, 3, 10)
DOMAIN = "brightleaf.example"
NAMES = ["priya", "ravi", "anu", "karthik", "meena", "arjun", "divya", "sanjay"]
STAFF = [Employee(f"{n}@{DOMAIN}", n.title(), f"{n.upper()}-LAPTOP", "India", 9, 18, is_admin=n == "ravi",
                  files_per_day=60) for n in NAMES]
PRIYA = STAFF[0].email


def ev(minutes, user=PRIYA, action="file_open", **fields):
    """One event, `minutes` after 10:00 on DAY, from the person's own laptop in the office."""
    return {
        "time": DAY + timedelta(hours=10, minutes=minutes),
        "user": user,
        "ip": OFFICE,
        "device": user.split("@")[0].upper() + "-LAPTOP",
        "country": "India",
        "action": action,
        **fields,
    }


@pytest.fixture(scope="session")
def profiles():
    """Harish's eight people at the simulated company."""
    return employee_profiles()


@pytest.fixture(scope="session")
def normal_day():
    return to_frame(build_scenario("normal_day"))


@pytest.fixture(scope="session")
def takeover():
    return to_frame(build_scenario("account_takeover"))
