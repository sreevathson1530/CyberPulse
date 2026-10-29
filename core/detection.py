"""Detection rules: each one looks for one warning sign in the log.

`Detector` reads events one at a time, oldest first, the way they arrive
during live playback, and returns the warning signs each event raises.
`detect()` runs it over a whole log at once.
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import timedelta

import pandas as pd

from core.schema import OFFICE_IPS, to_frame

# Tune these with Harish's data until a normal day shows no red alerts.
FAILED_LOGINS = 5                               # rule 1: wrong passwords on one account
FAILED_LOGIN_WINDOW = timedelta(minutes=10)     # ...within this time
SPRAY_ACCOUNTS = 4                              # rule 2: accounts one IP tries
SPRAY_WINDOW = timedelta(minutes=30)            # ...within this time
SUCCESS_LOOKBACK = timedelta(minutes=15)        # rule 3: how far back "straight after" reaches
FILE_WINDOW = timedelta(minutes=30)             # rule 6: files counted over this time
FILE_BURST_MIN = 40                             # ...this many is always too many
FILE_BURST_FACTOR = 3                           # ...or this many times the person's usual pace
ODD_HOURS_GRACE = timedelta(hours=1)            # rule 7: slack around working hours
BIG_UPLOAD_MB = 500                             # rule 9: megabytes uploaded
UPLOAD_WINDOW = timedelta(hours=1)              # ...within this time
MASS_RENAMES = 100                              # rule 10: files renamed
RENAME_WINDOW = timedelta(minutes=5)            # ...within this time
REPEAT_COOLDOWN = timedelta(hours=1)            # the same sign is not raised twice within this time
DEFAULT_WORK_HOURS = (8, 19)                    # for people with no profile
DEFAULT_FILES_PER_DAY = 50

# Every rule, and the step name it shows on the incident timeline.
RULES = {
    # The six must-haves
    "brute_force": "Password guessing",
    "password_spray": "One IP trying many accounts",
    "login_after_failures": "Login after failed attempts",
    "new_device_or_country": "Login from new device or country",
    "made_admin": "Made admin",
    "mass_file_access": "Mass file access",
    # The four extras
    "odd_hours_login": "Login at an odd hour",
    "external_forwarding": "Mail forwarded outside",
    "big_upload": "Big upload",
    "mass_rename": "Mass file renaming",
}

SEVERITIES = ("Low", "Medium", "High", "Critical")


@dataclass
class WarningSign:
    """One suspicious thing a rule spotted."""

    rule: str             # which rule raised it, a key of RULES
    step: str             # short label for the timeline, e.g. "Made admin"
    severity: str         # "Low", "Medium", "High" or "Critical"
    time: pd.Timestamp    # when it was spotted
    users: list[str]      # accounts involved
    ip: str
    device: str
    detail: str           # one plain-English sentence
    event_ids: list[str] = field(default_factory=list)  # the evidence


class Detector:
    """Reads events one by one and remembers what the rules need between them."""

    def __init__(self, employees=None, office_ips=OFFICE_IPS):
        self.profiles = {e.email: e for e in employees or []}
        self.admins = {e.email for e in self.profiles.values() if e.is_admin}
        self.office_ips = set(office_ips)

        # Devices and countries each person has signed in from: seeded from
        # their profile, then learned from every successful login.
        self.known_devices = defaultdict(set)
        self.known_countries = defaultdict(set)
        for e in self.profiles.values():
            self.known_devices[e.email].add(e.device)
            self.known_countries[e.email].add(e.country)

        # Recent events for the rules that count, oldest first.
        self.failures_by_user = defaultdict(deque)  # (time, event_id)
        self.failures_by_ip = defaultdict(deque)    # (time, user, event_id)
        self.files_by_user = defaultdict(deque)     # per (user, device): (time, event_id)
        self.uploads_by_user = defaultdict(deque)   # (time, size_mb, event_id)
        self.renames_by_user = defaultdict(deque)   # (time, event_id)

        # The last sign each rule raised, per account or IP.
        self.last_sign = {}

    def feed(self, e) -> list[WarningSign]:
        """Check one event (a row from to_frame(...).itertuples()) against
        every rule and return the new warning signs."""
        if e.action == "login" and e.outcome == "failure":
            return self._brute_force(e) + self._password_spray(e)
        if e.outcome != "success":
            return []
        if e.action == "login":
            return self._login_after_failures(e) + self._new_device_or_country(e) + self._odd_hours_login(e)
        if e.action == "admin_granted":
            return self._made_admin(e)
        if e.action in ("file_open", "file_download"):
            return self._mass_file_access(e)
        if e.action == "mail_forward_rule":
            return self._external_forwarding(e)
        if e.action == "file_upload":
            return self._big_upload(e)
        if e.action == "file_rename":
            return self._mass_rename(e)
        return []

    # The six must-have rules

    def _brute_force(self, e):
        """Rule 1: 5 wrong passwords on one account within 10 minutes."""
        recent = self.failures_by_user[e.user]
        _remember(recent, (e.time, e.event_id), e.time, max(FAILED_LOGIN_WINDOW, SUCCESS_LOOKBACK))
        in_window = [eid for t, eid in recent if e.time - t <= FAILED_LOGIN_WINDOW]
        if len(in_window) < FAILED_LOGINS:
            return []
        detail = f"{len(in_window)} wrong passwords for {e.user} within {_minutes(FAILED_LOGIN_WINDOW)}."
        return self._raise("brute_force", e.user, e, "Medium", detail, in_window)

    def _password_spray(self, e):
        """Rule 2: one IP address trying 4 or more different accounts."""
        recent = self.failures_by_ip[e.ip]
        _remember(recent, (e.time, e.user, e.event_id), e.time, max(SPRAY_WINDOW, SUCCESS_LOOKBACK))
        in_window = [(user, eid) for t, user, eid in recent if e.time - t <= SPRAY_WINDOW]
        accounts = {user for user, _ in in_window}
        if len(accounts) < SPRAY_ACCOUNTS:
            return []
        detail = f"{e.ip} tried {len(accounts)} different accounts within {_minutes(SPRAY_WINDOW)}."
        # No users: the sign is about the IP, and linking on every account it
        # tried would pull their unrelated activity into this incident.
        return self._raise("password_spray", e.ip, e, "High", detail, [eid for _, eid in in_window], users=[])

    def _login_after_failures(self, e):
        """Rule 3: a successful login straight after those failures."""
        since = e.time - SUCCESS_LOOKBACK
        on_account = [eid for t, eid in self.failures_by_user[e.user] if t >= since]
        from_ip = []
        if e.ip not in self.office_ips:
            from_ip = [eid for t, _, eid in self.failures_by_ip[e.ip] if t >= since]
        failures = max(on_account, from_ip, key=len)
        if len(failures) < FAILED_LOGINS:
            return []
        self.failures_by_user[e.user].clear()
        detail = f"{e.user} signed in right after {len(failures)} failed attempts."
        return self._raise("login_after_failures", e.user, e, "High", detail, failures + [e.event_id])

    def _new_device_or_country(self, e):
        """Rule 4: a login from a device or country the person has never used."""
        devices, countries = self.known_devices[e.user], self.known_countries[e.user]
        nothing_to_compare = not devices  # no profile and no earlier login
        new_device, new_country = e.device not in devices, e.country not in countries
        devices.add(e.device)
        countries.add(e.country)
        if nothing_to_compare or not (new_device or new_country):
            return []
        if new_device and new_country:
            what, severity = "new device and country", "High"
        elif new_device:
            what, severity = "new device", "Medium"
        else:
            what, severity = "new country", "Medium"
        detail = f"{e.user} signed in from a {what}: {e.device} in {e.country}."
        return self._raise("new_device_or_country", (e.user, e.device, e.country), e, severity, detail,
                           [e.event_id], step=f"Login from {what}")

    def _made_admin(self, e):
        """Rule 5: someone suddenly made an admin."""
        target = e.target or e.user
        to_self = target == e.user
        not_admin = bool(self.profiles) and e.user not in self.admins
        odd_time = self._outside_hours(e)
        self.admins.add(target)
        severity = "Critical" if to_self or not_admin or odd_time else "High"
        notes = []
        if not_admin:
            notes.append("without being an admin")
        if odd_time:
            notes.append(f"at {e.time:%H:%M}, outside working hours")
        detail = f"{e.user} gave {'their own account' if to_self else target} admin rights"
        detail += (" " + " and ".join(notes) if notes else "") + "."
        return self._raise("made_admin", target, e, severity, detail, [e.event_id], users=_unique([e.user, target]))

    def _mass_file_access(self, e):
        """Rule 6: far more files opened than the person's normal day.
        Counted per device, so the real person working on their own laptop
        is kept apart from an intruder using their account elsewhere."""
        recent = self.files_by_user[(e.user, e.device)]
        _remember(recent, (e.time, e.event_id), e.time, FILE_WINDOW)
        if len(recent) < self._file_limit(e.user):
            return []
        detail = (f"{e.user} opened or downloaded {len(recent)} files on {e.device} within "
                  f"{_minutes(FILE_WINDOW)}, far more than usual.")
        return self._raise("mass_file_access", (e.user, e.device), e, "High", detail, [eid for _, eid in recent])

    # The four extra rules

    def _odd_hours_login(self, e):
        """Extra rule 7: a login at an odd hour for this person."""
        if not self._outside_hours(e):
            return []
        detail = f"{e.user} signed in at {e.time:%H:%M}, outside their usual hours."
        return self._raise("odd_hours_login", e.user, e, "Low", detail, [e.event_id])

    def _external_forwarding(self, e):
        """Extra rule 8: a mail rule forwarding email outside the company."""
        if e.target and _domain(e.target) == _domain(e.user):
            return []
        detail = f"{e.user} added a rule forwarding their email to {e.target or 'an unknown address'}, outside the company."
        return self._raise("external_forwarding", (e.user, e.target), e, "High", detail, [e.event_id])

    def _big_upload(self, e):
        """Extra rule 9: a big upload."""
        recent = self.uploads_by_user[e.user]
        _remember(recent, (e.time, e.size_mb, e.event_id), e.time, UPLOAD_WINDOW)
        total = sum(mb for _, mb, _ in recent)
        if total < BIG_UPLOAD_MB:
            return []
        detail = f"{e.user} uploaded {total:,.0f} MB within {_minutes(UPLOAD_WINDOW)}."
        return self._raise("big_upload", e.user, e, "High", detail, [eid for _, _, eid in recent])

    def _mass_rename(self, e):
        """Extra rule 10: 100+ files renamed in 5 minutes, the mark of ransomware."""
        recent = self.renames_by_user[e.user]
        _remember(recent, (e.time, e.event_id), e.time, RENAME_WINDOW)
        if len(recent) < MASS_RENAMES:
            return []
        detail = f"{len(recent)} files renamed by {e.user} within {_minutes(RENAME_WINDOW)}."
        return self._raise("mass_rename", e.user, e, "Critical", detail, [eid for _, eid in recent])

    # Helpers

    def _raise(self, rule, key, e, severity, detail, event_ids, step=None, users=None):
        """Create a warning sign. If the same rule already fired for the same
        key within REPEAT_COOLDOWN, add the evidence to that sign instead, so
        a long attack shows up once on the timeline."""
        last = self.last_sign.get((rule, key))
        if last and e.time - last.time <= REPEAT_COOLDOWN:
            last.event_ids = _unique(last.event_ids + event_ids)
            return []
        sign = WarningSign(rule=rule, step=step or RULES[rule], severity=severity, time=e.time,
                           users=[e.user] if users is None else users, ip=e.ip, device=e.device,
                           detail=detail, event_ids=_unique(event_ids))
        self.last_sign[(rule, key)] = sign
        return [sign]

    def _outside_hours(self, e):
        profile = self.profiles.get(e.user)
        start, end = (profile.work_start, profile.work_end) if profile else DEFAULT_WORK_HOURS
        day = e.time.normalize()
        opens = day + timedelta(hours=start) - ODD_HOURS_GRACE
        closes = day + timedelta(hours=end) + ODD_HOURS_GRACE
        return not opens <= e.time <= closes

    def _file_limit(self, user):
        """How many files in FILE_WINDOW is far more than this person's usual pace."""
        profile = self.profiles.get(user)
        if profile:
            per_day, hours = profile.files_per_day, profile.work_end - profile.work_start
        else:
            per_day, hours = DEFAULT_FILES_PER_DAY, DEFAULT_WORK_HOURS[1] - DEFAULT_WORK_HOURS[0]
        usual = per_day / max(hours, 1) * (FILE_WINDOW / timedelta(hours=1))
        return max(FILE_BURST_MIN, round(FILE_BURST_FACTOR * usual))


def detect(events, employees=None, office_ips=OFFICE_IPS) -> list[WarningSign]:
    """Run every rule over a whole log. Returns the warning signs, oldest first."""
    detector = Detector(employees, office_ips)
    signs = []
    for event in to_frame(events).itertuples(index=False):
        signs += detector.feed(event)
    return signs


def _remember(queue, item, now, keep):
    """Add item to a time-ordered queue and forget entries older than keep."""
    queue.append(item)
    while now - queue[0][0] > keep:
        queue.popleft()


def _domain(address):
    return address.rsplit("@", 1)[-1].lower()


def _minutes(span):
    return f"{int(span.total_seconds() // 60)} minutes"


def _unique(items):
    return list(dict.fromkeys(items))
