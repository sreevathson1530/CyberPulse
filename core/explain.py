"""Plain-English explanations: what happened, why it matters, what to do now.

Owner: Keerthana (testing and presentation). This first version was written
while connecting the app, so the What happened screen shows real text.
Change the wording freely; keep one entry per kind in ATTACK_KINDS.
"""

from core.correlation import ATTACK_KINDS

# For each kind of attack: why it matters, and what to do now.
# "What happened" is built from the incident itself, in what_happened().
WHY_AND_WHAT_TO_DO = {
    "Ransomware": (
        "This is how ransomware locks a company's files: they stop opening until a ransom is paid.",
        "Unplug that computer from the network now, lock the account and restore the files from backup.",
    ),
    "Account takeover": (
        "Whoever is in can read and send email as this person, open company files and, with admin rights, change anything.",
        "Lock the account, sign out all its sessions and remove any forwarding rule, then reset the password and phone the person to check.",
    ),
    "Email forwarding": (
        "Invoice fraud often starts this way: an outsider reads payment emails, then sends fake bank details.",
        "Remove the rule and ask the person whether they set it up. If they did not, reset their password.",
    ),
    "Data theft": (
        "Large uploads can mean company data is leaving the business.",
        "Ask the person what they uploaded and where. If they cannot say, lock the account.",
    ),
    "Unusual file activity": (
        "It may be a busy day, such as month-end reports, or someone copying files they should not.",
        "Check with the person. If it was not them, lock the account and sign out all its sessions.",
    ),
    "Password guessing": (
        "Guessing is how attackers break into accounts with weak passwords.",
        "Check the person can still sign in, ask them to choose a stronger password and turn on two-step sign-in.",
    ),
    "New admin": (
        "Admin rights let an account change settings, add users and read anything.",
        "Check the change was planned, for example with an IT ticket. If not, remove the rights and lock the account.",
    ),
    "Unusual login": (
        "It is often travel, a new laptop or late work, but it can be someone else using the password.",
        "Check with the person. If it was not them, sign out all sessions and reset the password.",
    ),
}

assert set(WHY_AND_WHAT_TO_DO) == set(ATTACK_KINDS), "every kind needs an explanation"


def explain(incident) -> dict:
    """Three plain sentences about an incident, plus a title."""
    why, what_to_do = WHY_AND_WHAT_TO_DO[incident.kind]
    if incident.level == "Watch":
        why = f"On its own this is low risk. {why}"
    return {
        "title": f"{incident.kind} · {incident.level}",
        "what_happened": what_happened(incident),
        "why_it_matters": why,
        "what_to_do": what_to_do,
    }


def what_happened(incident) -> str:
    """One or two sentences, built from the incident's warning signs."""
    signs = {sign.rule: sign for sign in incident.signs}
    who = _name(incident.users[0]) if incident.users else "an unknown account"
    way_in = signs.get("new_device_or_country") or signs.get("login_after_failures")

    if incident.kind == "Account takeover" and way_in:
        after = [step.lower() for step in incident.steps if step not in (way_in.step, "Password guessing",
                                                                         "One IP trying many accounts",
                                                                         "Login after failed attempts")]
        start = f"Someone signed in to {who}'s account from {way_in.device} in {way_in.country}"
        if "login_after_failures" in signs:
            start += " after guessing the password"
        return start + (f", then: {', '.join(after)}." if after else ".")
    return _detail(incident)


def _detail(incident):
    """The first warning sign's own sentence, with names instead of emails."""
    text = incident.signs[0].detail
    for user in incident.users:
        text = text.replace(user, _name(user))
    return text


def _name(email):
    """anita.rao@cyberpulse.example -> Anita Rao"""
    return email.split("@")[0].replace(".", " ").title()
