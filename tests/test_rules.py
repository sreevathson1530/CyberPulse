"""Each detection rule fires on a clear case and stays quiet on a near miss."""

import pytest

from conftest import ATTACKER, DOMAIN, PRIYA, STAFF, ev
from core.detection import RULES, detect

AWAY = {"ip": ATTACKER, "device": "DESKTOP-X9", "country": "Netherlands"}

# rule: (events that should raise it, near miss that should not)
CASES = {
    "brute_force": (
        [ev(i, action="login", outcome="failure") for i in range(5)],
        [ev(3 * i, action="login", outcome="failure") for i in range(5)],  # spread over 12 minutes
    ),
    "password_spray": (
        [ev(i, s.email, "login", outcome="failure", ip=ATTACKER) for i, s in enumerate(STAFF[:4])],
        [ev(i, s.email, "login", outcome="failure", ip=ATTACKER) for i, s in enumerate(STAFF[:3])],
    ),
    "login_after_failures": (
        [ev(i, action="login", outcome="failure") for i in range(5)] + [ev(6, action="login")],
        [ev(i, action="login", outcome="failure") for i in range(2)] + [ev(3, action="login")],  # a typo
    ),
    "new_device_or_country": (
        [ev(0, action="login", device="DESKTOP-X9")],
        [ev(0, action="login")],
    ),
    "made_admin": (
        [ev(0, action="admin_granted", target=PRIYA)],
        [ev(0, action="file_open")],
    ),
    "mass_file_access": (
        [ev(i / 3, action="file_download") for i in range(45)],  # 45 files in 15 minutes
        [ev(i, action="file_download") for i in range(45)],      # 45 files in 45 minutes
    ),
    "odd_hours_login": (
        [ev(-7 * 60, action="login")],  # 03:00
        [ev(-90, action="login")],      # 08:30, inside the grace hour
    ),
    "external_forwarding": (
        [ev(0, action="mail_forward_rule", target="collect@mailbox.example")],
        [ev(0, action="mail_forward_rule", target=f"ravi@{DOMAIN}")],
    ),
    "big_upload": (
        [ev(0, action="file_upload", size_mb=300), ev(20, action="file_upload", size_mb=250)],
        [ev(0, action="file_upload", size_mb=300), ev(90, action="file_upload", size_mb=250)],
    ),
    "mass_rename": (
        [ev(i / 30, action="file_rename") for i in range(100)],  # 100 renames in under 4 minutes
        [ev(i / 15, action="file_rename") for i in range(100)],  # 100 renames in over 6 minutes
    ),
}


def rules_raised(events, employees=STAFF):
    return {sign.rule for sign in detect(events, employees)}


def test_every_rule_has_a_case():
    assert set(CASES) == set(RULES)


@pytest.mark.parametrize("rule", list(CASES))
def test_rule_fires(rule):
    fires, _ = CASES[rule]
    assert rule in rules_raised(fires)


@pytest.mark.parametrize("rule", list(CASES))
def test_rule_stays_quiet_on_near_miss(rule):
    _, quiet = CASES[rule]
    assert rule not in rules_raised(quiet)


@pytest.mark.parametrize("rule", list(CASES))
def test_rule_works_without_profiles(rule):
    fires, _ = CASES[rule]
    if rule == "new_device_or_country":
        fires = [ev(-30, action="login")] + fires  # without a profile, the first login sets what is normal
    assert rule in rules_raised(fires, employees=None)


def test_rules_never_read_the_answer_key():
    events = CASES["brute_force"][0]
    labelled = [dict(e, label="attack") for e in events]
    assert [s.detail for s in detect(events, STAFF)] == [s.detail for s in detect(labelled, STAFF)]


def test_repeats_extend_one_sign_instead_of_adding_more():
    events = [ev(i / 3, action="file_download") for i in range(120)]
    signs = [s for s in detect(events, STAFF) if s.rule == "mass_file_access"]
    assert len(signs) == 1
    assert len(signs[0].event_ids) > 45


def test_mass_files_cannot_be_hidden_by_switching_devices():
    devices = ["DESKTOP-A", "DESKTOP-B", "DESKTOP-C", "DESKTOP-D"]
    events = [ev(i / 3, action="file_download", device=devices[i % 4], **{k: v for k, v in AWAY.items() if k != "device"})
              for i in range(45)]
    assert "mass_file_access" in rules_raised(events)


def test_mass_file_evidence_leaves_out_the_persons_own_laptop():
    own = [ev(i / 2, action="file_open") for i in range(20)]
    intruder = [ev(i / 2 + 0.1, action="file_download", **AWAY) for i in range(30)]
    sign = next(s for s in detect(own + intruder, STAFF) if s.rule == "mass_file_access")
    assert "not their usual laptop" in sign.detail
    assert len(sign.event_ids) == 30


def test_admin_grant_by_an_admin_in_working_hours_is_high_not_critical():
    sign, = detect([ev(0, "ravi@" + DOMAIN, "admin_granted", target=PRIYA)], STAFF)
    assert sign.severity == "High"


@pytest.mark.parametrize("why, event", [
    ("to themselves", ev(0, action="admin_granted", target=PRIYA)),
    ("by a non-admin", ev(0, action="admin_granted", target="anu@" + DOMAIN)),
    ("at night", ev(12 * 60, "ravi@" + DOMAIN, "admin_granted", target=PRIYA)),
])
def test_risky_admin_grants_are_critical(why, event):
    sign, = detect([event], STAFF)
    assert sign.severity == "Critical", why


def test_failed_logins_from_the_shared_office_ip_are_not_blamed_on_the_next_login():
    typos = [ev(i / 4, s.email, "login", outcome="failure") for i, s in enumerate(STAFF[1:6])]
    assert "login_after_failures" not in rules_raised(typos + [ev(2, action="login")])
