"""What one log event looks like.

The whole team agrees on this format on day one. Harish's simulator writes
events in this shape, the backend rules read it, and Aswin's screens show it.
Change it only when all four of us agree.
"""

from dataclasses import asdict, dataclass
from datetime import datetime

import pandas as pd

# Every event has these columns, in this order.
COLUMNS = [
    "event_id",  # unique id, e.g. "E00001"
    "time",      # when it happened
    "user",      # account that did it, e.g. "priya@brightleaf.example"
    "ip",        # IP address it came from (203.0.113.x test range only)
    "device",    # device name, e.g. "PRIYA-LAPTOP"
    "country",   # two-letter country code, e.g. "IN"
    "action",    # one of ACTIONS below
    "outcome",   # "success" or "failure"
    "target",    # what it touched: a file name, an email address or an account
    "size_mb",   # data moved in megabytes, for uploads and downloads
    "label",     # "normal" or "attack": the answer key. The rules never read it.
]

# What a person can do, and how the screens describe it.
ACTIONS = {
    "login": "Signed in",
    "logout": "Signed out",
    "password_reset": "Reset their password",
    "file_open": "Opened a file",
    "file_download": "Downloaded a file",
    "file_upload": "Uploaded a file",
    "file_rename": "Renamed a file",
    "email_send": "Sent an email",
    "mail_forward_rule": "Added a mail forwarding rule",
    "admin_granted": "Gave admin rights",  # target = the account made admin
}

OUTCOMES = ("success", "failure")
LABELS = ("normal", "attack")

# The office's shared internet address. Everyone in the office signs in from
# it, so it says nothing about who is behind an event.
OFFICE_IPS = {"203.0.113.10"}

REQUIRED = ["time", "user", "ip", "device", "country", "action"]
DEFAULTS = {"event_id": "", "outcome": "success", "target": "", "size_mb": 0.0, "label": "normal"}


@dataclass
class LogEvent:
    """One thing that happened, such as a sign-in or a file download."""

    time: datetime
    user: str
    ip: str
    device: str
    country: str
    action: str
    outcome: str = "success"
    target: str = ""
    size_mb: float = 0.0
    label: str = "normal"
    event_id: str = ""


@dataclass
class Employee:
    """A person at the fake company, and what is normal for them."""

    email: str
    name: str
    device: str             # their usual laptop
    country: str            # where they usually work from
    work_start: int = 9     # usual first working hour, 0-23
    work_end: int = 18      # usual last working hour, 0-23
    is_admin: bool = False  # allowed to give admin rights
    files_per_day: int = 50  # files they usually open or download in a day


def to_frame(events) -> pd.DataFrame:
    """Turn events (LogEvent objects, dicts or a DataFrame) into a clean
    DataFrame: every column present, times parsed, oldest first.

    Raises ValueError when a required column is missing or an action,
    outcome or label is not one we agreed on.
    """
    if isinstance(events, pd.DataFrame):
        df = events.copy()
    else:
        df = pd.DataFrame([asdict(e) if isinstance(e, LogEvent) else dict(e) for e in events])

    if df.empty:
        empty = pd.DataFrame(columns=COLUMNS)
        empty["time"] = pd.to_datetime(empty["time"])
        return empty

    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise ValueError(f"events are missing columns: {', '.join(missing)}")

    for column, value in DEFAULTS.items():
        if column not in df.columns:
            df[column] = value
        df[column] = df[column].fillna(value)

    df["time"] = pd.to_datetime(df["time"])
    df["size_mb"] = pd.to_numeric(df["size_mb"], errors="coerce").fillna(0.0)
    df = df.sort_values("time", kind="stable").reset_index(drop=True)

    no_id = df["event_id"] == ""
    df.loc[no_id, "event_id"] = [f"E{i + 1:05d}" for i in df.index[no_id]]

    _check_values(df, "action", ACTIONS)
    _check_values(df, "outcome", OUTCOMES)
    _check_values(df, "label", LABELS)
    return df[COLUMNS]


def _check_values(df, column, allowed):
    unknown = sorted(set(df[column]) - set(allowed))
    if unknown:
        raise ValueError(f"unknown {column}: {', '.join(map(str, unknown))}")
