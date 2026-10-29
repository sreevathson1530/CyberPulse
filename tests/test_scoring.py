"""Linking warning signs into incidents, the danger score and the attack kind."""

from types import SimpleNamespace

import pytest

from conftest import ATTACKER, PRIYA, STAFF, ev
from core.correlation import ATTACK_KINDS, analyze, attack_kind, danger_level, danger_score


def sign(rule, severity="Low"):
    return SimpleNamespace(rule=rule, severity=severity)


def test_score_examples():
    assert danger_score([sign("odd_hours_login", "Low")]) == 5
    assert danger_score([sign("made_admin", "Critical"), sign("a"), sign("b"), sign("c")]) == 70
    assert danger_score([sign(str(i), "Critical") for i in range(10)]) == 100
    assert danger_score([]) == 0


def test_repeated_rule_adds_no_extra_points():
    assert danger_score([sign("brute_force", "Medium"), sign("brute_force", "Medium")]) == 15


@pytest.mark.parametrize("score, level", [(0, "Clear"), (1, "Watch"), (39, "Watch"), (40, "Suspicious"),
                                          (74, "Suspicious"), (75, "Likely attack"), (100, "Likely attack")])
def test_levels(score, level):
    assert danger_level(score) == level


@pytest.mark.parametrize("rules, kind", [
    (["mass_rename"], "Ransomware"),
    (["login_after_failures", "new_device_or_country"], "Account takeover"),
    (["new_device_or_country", "external_forwarding"], "Account takeover"),
    (["external_forwarding"], "Email forwarding"),
    (["big_upload"], "Data theft"),
    (["mass_file_access"], "Unusual file activity"),
    (["brute_force", "login_after_failures"], "Password guessing"),
    (["made_admin"], "New admin"),
    (["odd_hours_login"], "Unusual login"),
])
def test_attack_kind(rules, kind):
    assert kind in ATTACK_KINDS
    assert attack_kind([sign(rule) for rule in rules]) == kind


def test_steps_of_one_attack_link_into_one_incident():
    away = {"ip": ATTACKER, "device": "DESKTOP-X9", "country": "Netherlands"}
    events = ([ev(i / 2, action="login", outcome="failure", **away) for i in range(6)]
              + [ev(4, action="login", **away),
                 ev(8, action="mail_forward_rule", target="collect@mailbox.example", **away),
                 ev(15, action="admin_granted", target=PRIYA, **away)])
    incidents = analyze(events, STAFF)
    assert len(incidents) == 1
    assert incidents[0].kind == "Account takeover"
    assert incidents[0].level == "Likely attack"


def test_people_sharing_the_office_ip_are_not_linked():
    events = [ev(0, action="login", device="NEW-LAPTOP"),
              ev(5, "anu@brightleaf.example", "mail_forward_rule", target="me@home.example")]
    assert len(analyze(events, STAFF)) == 2


def test_signs_hours_apart_are_separate_incidents():
    events = [ev(0, action="login", device="NEW-LAPTOP"),
              ev(4 * 60, action="mail_forward_rule", target="me@home.example")]
    assert len(analyze(events, STAFF)) == 2


def test_empty_log():
    assert analyze([]) == []
