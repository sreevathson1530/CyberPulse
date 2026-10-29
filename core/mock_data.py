"""CyberPulse Mock Attack & Normal Operating Telemetry Engine.

Generates realistic forensic event streams, multi-stage attack scenarios,
and benign baseline logs for out-of-the-box offline evaluation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pandas as pd


# Scenario identifiers
SCENARIO_NORMAL = "Normal Operating Day"
SCENARIO_ATTACK = "Account Takeover Attack"

SCENARIOS: List[str] = [
    SCENARIO_ATTACK,
    SCENARIO_NORMAL,
]

# Color codes following CyberPulse Dark Design System
COLOR_WATCH_BG = "#1E2D24"       # Sage Green muted background
COLOR_WATCH_ACCENT = "#4E8B65"   # Sage Green accent
COLOR_SUSPICIOUS_BG = "#2D2318"  # Amber muted background
COLOR_SUSPICIOUS_ACCENT = "#D97706" # Amber accent
COLOR_ATTACK_BG = "#381A1A"      # Crimson muted background
COLOR_ATTACK_ACCENT = "#DC2626"  # Crimson accent

SEVERITY_LEVEL_MAP = {
    "Info": 1,
    "Low": 2,
    "Medium": 3,
    "High": 4,
    "Critical": 5,
}

SEVERITY_COLOR_MAP = {
    "Info": "#64748B",      # Slate Gray
    "Low": "#4E8B65",       # Sage Green
    "Medium": "#EAB308",    # Yellow/Gold
    "High": "#D97706",      # Amber
    "Critical": "#DC2626",  # Crimson
}


def _get_danger_meta(score: int) -> Tuple[str, str, str]:
    """Calculate status badge, background color, and accent color from danger score."""
    if score < 40:
        return "[WATCH]", COLOR_WATCH_BG, COLOR_WATCH_ACCENT
    elif score < 75:
        return "[SUSPICIOUS]", COLOR_SUSPICIOUS_BG, COLOR_SUSPICIOUS_ACCENT
    else:
        return "[LIKELY ATTACK]", COLOR_ATTACK_BG, COLOR_ATTACK_ACCENT


# Pre-defined simulation steps for Account Takeover Attack
ATTACK_STEPS: List[Dict[str, Any]] = [
    {
        "step_index": 1,
        "stage_title": "Stage 1/5: Credential Spray & Brute Force",
        "danger_score": 34,
        "new_event": {
            "Timestamp": "2026-10-29 02:14:12",
            "time_seq": "02:14:12",
            "User": "sarah.chen@acme-corp.com",
            "Action": "5x Wrong Password (Brute Force)",
            "IP Address": "185.220.101.44",
            "Device": "Tor Exit Node (Unknown Browser)",
            "Country": "Netherlands",
            "Flagged Severity": "Medium",
            "is_suspicious": True,
            "Log_Line": "[02:14:12] WARN [AUTH_SERVICE] 5 consecutive failed authentication attempts for 'sarah.chen@acme-corp.com' from TOR exit IP 185.220.101.44.",
        },
        "story": {
            "title": "Initial Infiltration Probing Detected",
            "narrative": (
                "**Keerthana's Incident Brief:** An automated credential spray pattern was detected "
                "originating from a known Dutch Tor exit node (185.220.101.44). The attacker attempted multiple "
                "dictionary passwords against Sarah Chen's Microsoft 365 cloud credentials within a 45-second window."
            ),
            "impact": [
                "Targeted account: `sarah.chen@acme-corp.com` (Senior Finance Director).",
                "Authentication failed 5 times before temporary lockout threshold triggered.",
                "Zero internal systems breached at this preliminary stage.",
            ],
            "recommendations": [
                "Verify whether Sarah Chen reported forgotten credentials or traveling abroad.",
                "Enforce immediate FIDO2 hardware token MFA requirement.",
                "Monitor for secondary ingress attempts bypassing geofencing.",
            ],
        },
    },
    {
        "step_index": 2,
        "stage_title": "Stage 2/5: Unauthorized Session Established",
        "danger_score": 64,
        "new_event": {
            "Timestamp": "2026-10-29 02:48:30",
            "time_seq": "02:48:30",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Login from New Device (Russia)",
            "IP Address": "94.25.182.11",
            "Device": "Linux x86_64 / Chrome 128 (Unregistered)",
            "Country": "Russia",
            "Flagged Severity": "High",
            "is_suspicious": True,
            "Log_Line": "[02:48:30] ALERT [SSO_GATEWAY] Successful login from anomalous location (Moscow, RU - 94.25.182.11). Device hash unlinked to employee hardware asset registry.",
        },
        "story": {
            "title": "Impossible Travel & Rogue Device Session",
            "narrative": (
                "**Keerthana's Incident Brief:** An authenticated session was established for Sarah Chen from Moscow, Russia. "
                "Just 34 minutes prior, Sarah's corporate laptop was in New York. The connection bypassed legacy SMS MFA "
                "via session token replay stolen from a compromised third-party browser cookie."
            ),
            "impact": [
                "Attacker successfully assumed identity as Sarah Chen.",
                "Unregistered Linux client gained valid OAuth 2.0 refresh bearer tokens.",
                "High likelihood of corporate mail and OneDrive read permissions.",
            ],
            "recommendations": [
                "**Immediate Action:** Execute `Sign Out All Sessions` to revoke valid refresh tokens.",
                "Revoke OAuth app consent grants issued in the last 2 hours.",
                "Notify IT Security on-call administrator.",
            ],
        },
    },
    {
        "step_index": 3,
        "stage_title": "Stage 3/5: Persistence Established",
        "danger_score": 86,
        "new_event": {
            "Timestamp": "2026-10-29 03:02:15",
            "time_seq": "03:02:15",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Created Forwarding Rule",
            "IP Address": "94.25.182.11",
            "Device": "Linux x86_64 / Chrome 128",
            "Country": "Russia",
            "Flagged Severity": "Critical",
            "is_suspicious": True,
            "Log_Line": "[03:02:15] CRIT [EXCHANGE_ONLINE] New inbox rule 'Invoice_Sync_2026' created: Forward all messages containing 'wire', 'invoice', 'ACH' to external address 'billing-audit@darkbox-mail.com'.",
        },
        "story": {
            "title": "Covert Email Exfiltration Rule Configured",
            "narrative": (
                "**Keerthana's Incident Brief:** The adversary configured a silent, persistent mailbox rule named "
                "`Invoice_Sync_2026` inside Sarah's Exchange account. Every email containing keywords such as "
                "`wire`, `invoice`, `routing`, or `payment` is now automatically mirrored to an untrusted external "
                "address (`billing-audit@darkbox-mail.com`) and then marked as read to evade notice."
            ),
            "impact": [
                "Active Business Email Compromise (BEC) stage reached.",
                "Direct risk of fraudulent wire redirection and customer payment diversion.",
                "Outgoing and incoming confidential customer billing threads exposed.",
            ],
            "recommendations": [
                "**Critical Mitigation:** Execute `Remove Forwarding Rule` immediately.",
                "**Account Lockdown:** Click `Lock Account` to sever attacker's active mailbox control.",
                "Alert finance department to suspend pending outbound wire releases pending audit.",
            ],
        },
    },
    {
        "step_index": 4,
        "stage_title": "Stage 4/5: Internal Reconnaissance & Escalation",
        "danger_score": 93,
        "new_event": {
            "Timestamp": "2026-10-29 03:22:04",
            "time_seq": "03:22:04",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Privilege Escalation & Mailbox Scan",
            "IP Address": "94.25.182.11",
            "Device": "PowerShell Core 7.4 / Linux",
            "Country": "Russia",
            "Flagged Severity": "Critical",
            "is_suspicious": True,
            "Log_Line": "[03:22:04] CRIT [GRAPH_API] High-velocity bulk query against MS Graph API: 1,420 user directory objects read. Unauthorized role elevation request submitted for 'Company Administrator'.",
        },
        "story": {
            "title": "High-Velocity Tenant Enumeration",
            "narrative": (
                "**Keerthana's Incident Brief:** Using scripted automated Graph API queries, the attacker surveyed "
                "the entire organizational tenant directory, pulling contact lists, executive org charts, and attempting "
                "to assign Azure AD Global Administrator roles to a newly spun backdoor account."
            ),
            "impact": [
                "1,420 employee records and internal phone numbers harvested.",
                "Failed privilege elevation attempt logged against Azure AD Privileged Identity Management (PIM).",
                "Secondary accounts targeted for simultaneous lateral movement.",
            ],
            "recommendations": [
                "Isolate all endpoints linked to recent credential caches.",
                "Initiate forensic snapshot of Sarah Chen's Azure sign-in telemetry.",
                "Deploy conditional access policy restricting tenant administration to trusted hardware.",
            ],
        },
    },
    {
        "step_index": 5,
        "stage_title": "Stage 5/5: Mass Exfiltration Detected",
        "danger_score": 99,
        "new_event": {
            "Timestamp": "2026-10-29 03:45:51",
            "time_seq": "03:45:51",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Exfiltrated 250 Files (Payroll/Tax)",
            "IP Address": "94.25.182.11",
            "Device": "PowerShell Core 7.4 / Linux",
            "Country": "Russia",
            "Flagged Severity": "Critical",
            "is_suspicious": True,
            "Log_Line": "[03:45:51] CRIT [DATALOSS_PREVENTION] Mass archive download: 250 confidential files (4.2 GB) exfiltrated from 'Confidential Finance / 2026 Tax & Payroll'. Destination IP 94.25.182.11.",
        },
        "story": {
            "title": "Severe Data Breach & Extortion Threat",
            "narrative": (
                "**Keerthana's Incident Brief:** The adversary initiated rapid bulk exfiltration of 250 confidential "
                "financial spreadsheets, employee W-2 records, and customer contracts totaling 4.2 GB. CyberPulse "
                "early-warning tripwires flagged the anomalous egress speed 3 hours and 15 minutes before ransomware "
                "could be staged on internal network shares."
            ),
            "impact": [
                "250 sensitive files downloaded offsite.",
                "Potential PII regulatory reporting requirements (GDPR / CCPA / HIPAA).",
                "Substantial legal liability unless mitigated and contained instantly.",
            ],
            "recommendations": [
                "Execute full response suite: `Lock Account`, `Sign Out All Sessions`, `Remove Forwarding Rule`.",
                "Engage incident response legal counsel and cyber insurance carrier.",
                "Initiate external egress firewall block for subnet `94.25.182.0/24`.",
            ],
        },
    },
]

# Pre-defined simulation steps for Normal Operating Day
NORMAL_STEPS: List[Dict[str, Any]] = [
    {
        "step_index": 1,
        "stage_title": "Stage 1/5: Routine Morning Authentication",
        "danger_score": 8,
        "new_event": {
            "Timestamp": "2026-10-29 08:30:10",
            "time_seq": "08:30:10",
            "User": "sarah.chen@acme-corp.com",
            "Action": "SSO Login Verified (MFA OK)",
            "IP Address": "64.124.8.19",
            "Device": "MacBookPro18,1 / macOS 15.1",
            "Country": "United States",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[08:30:10] INFO [SSO_GATEWAY] Standard corporate SSO authentication successful for 'sarah.chen@acme-corp.com'. FIDO2 passkey approved.",
        },
        "story": {
            "title": "Baseline Verified Employee Login",
            "narrative": (
                "**Keerthana's Incident Brief:** Clean, expected morning login activity. Sarah Chen authenticated "
                "from the corporate HQ office in New York via company-managed MacBook hardware. FIDO2 biometric "
                "verification succeeded with zero anomalies."
            ),
            "impact": [
                "Zero anomalies detected.",
                "Standard operational security posture maintained.",
                "All device compliance certificates up to date.",
            ],
            "recommendations": [
                "No intervention required. System is operating normally.",
            ],
        },
    },
    {
        "step_index": 2,
        "stage_title": "Stage 2/5: Normal Document Collaboration",
        "danger_score": 12,
        "new_event": {
            "Timestamp": "2026-10-29 09:15:44",
            "time_seq": "09:15:44",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Opened Q3 Budget Sheet",
            "IP Address": "64.124.8.19",
            "Device": "MacBookPro18,1 / Safari 18",
            "Country": "United States",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[09:15:44] INFO [SHAREPOINT] Sarah Chen opened 'Q3_Operating_Budget.xlsx' in Office 365 Web App. Access verified against finance group ACL.",
        },
        "story": {
            "title": "Authorized Business Document Access",
            "narrative": (
                "**Keerthana's Incident Brief:** Standard document collaboration recorded. The access was verified "
                "against Sarah's role-based permissions in the Finance group. Audit telemetry confirms benign browsing."
            ),
            "impact": [
                "Routine day-to-day productivity.",
                "No abnormal data movement.",
            ],
            "recommendations": [
                "Maintain continuous baseline anomaly monitoring.",
            ],
        },
    },
    {
        "step_index": 3,
        "stage_title": "Stage 3/5: Mobile Push & Device Sync",
        "danger_score": 15,
        "new_event": {
            "Timestamp": "2026-10-29 10:02:19",
            "time_seq": "10:02:19",
            "User": "david.kim@acme-corp.com",
            "Action": "Corporate Email Sync (iOS)",
            "IP Address": "172.56.21.84",
            "Device": "iPhone 15 Pro / iOS 18.1",
            "Country": "United States",
            "Flagged Severity": "Low",
            "is_suspicious": False,
            "Log_Line": "[10:02:19] INFO [MDM_ENROLLMENT] Routine Exchange ActiveSync heartbeat received from managed corporate device iPhone-DK-04.",
        },
        "story": {
            "title": "Healthy Mobile Device Telemetry",
            "narrative": (
                "**Keerthana's Incident Brief:** Expected mobile sync cycle from VP of Engineering David Kim. "
                "Device compliance checks validated disk encryption, passcode requirements, and OS patch levels."
            ),
            "impact": [
                "Device compliant with corporate MDM policy.",
                "No jailbreak or sideloading signatures present.",
            ],
            "recommendations": [
                "Continue standard zero-trust periodic evaluation.",
            ],
        },
    },
    {
        "step_index": 4,
        "stage_title": "Stage 4/5: Scheduled Payroll Batch Execution",
        "danger_score": 19,
        "new_event": {
            "Timestamp": "2026-10-29 11:45:00",
            "time_seq": "11:45:00",
            "User": "payroll-service-account@acme-corp.com",
            "Action": "Dispatched Bi-Weekly Payroll Batch",
            "IP Address": "10.0.4.15",
            "Device": "ERP Core Engine / Linux",
            "Country": "United States",
            "Flagged Severity": "Low",
            "is_suspicious": False,
            "Log_Line": "[11:45:00] INFO [ERP_PAYROLL] Scheduled batch #4409 executed successfully via internal VPC. 48 direct deposits dispatched with signed hash verification.",
        },
        "story": {
            "title": "Automated Financial Task Execution",
            "narrative": (
                "**Keerthana's Incident Brief:** The internal ERP system completed its bi-weekly payroll calculation. "
                "All cryptographic signatures matched the authorized bank routing key repository."
            ),
            "impact": [
                "Scheduled operational task performed as expected.",
                "No unexpected external network calls detected.",
            ],
            "recommendations": [
                "No action needed.",
            ],
        },
    },
    {
        "step_index": 5,
        "stage_title": "Stage 5/5: Automated Backup Integrity Verification",
        "danger_score": 10,
        "new_event": {
            "Timestamp": "2026-10-29 13:00:22",
            "time_seq": "13:00:22",
            "User": "backup-admin@acme-corp.com",
            "Action": "Cloud Backup Snapshot Verified",
            "IP Address": "10.0.12.8",
            "Device": "Veeam Immutable Cloud Agent",
            "Country": "United States",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[13:00:22] INFO [BACKUP_DAEMON] Daily snapshot validation complete. Object storage immutable retention locked for 90 days. SHA-256 integrity check: PASSED.",
        },
        "story": {
            "title": "Clean Operational Day Verified",
            "narrative": (
                "**Keerthana's Incident Brief:** Normal operating day concluded cleanly. Immutable air-gapped "
                "backups are securely locked, all employee identities remain protected, and zero false-positive "
                "alerts were triggered by the early-warning correlation engine."
            ),
            "impact": [
                "Tenant health: 100% Secure.",
                "False positive rate: 0.00%.",
                "All business operations uninterrupted.",
            ],
            "recommendations": [
                "CyberPulse continues active surveillance.",
            ],
        },
    },
]


def get_scenario_data(scenario_name: str, step_idx: int) -> Dict[str, Any]:
    """Retrieve state snapshot for a given scenario and step number (1 to 5).

    Args:
        scenario_name: Either 'Normal Operating Day' or 'Account Takeover Attack'.
        step_idx: Step index between 1 and 5.

    Returns:
        Dictionary containing danger score, status badge, colors, timeline events,
        incident story narrative, and live log stream.
    """
    is_attack = scenario_name == SCENARIO_ATTACK
    raw_steps = ATTACK_STEPS if is_attack else NORMAL_STEPS

    # Bound step_idx safely
    step_idx = max(1, min(step_idx, len(raw_steps)))
    current_step_meta = raw_steps[step_idx - 1]

    # Gather cumulative events up to this step
    cumulative_events: List[Dict[str, Any]] = []
    accumulated_logs: List[str] = []

    for s in raw_steps[:step_idx]:
        event_dict = dict(s["new_event"])
        event_dict["severity_score"] = SEVERITY_LEVEL_MAP.get(event_dict["Flagged Severity"], 1)
        event_dict["severity_color"] = SEVERITY_COLOR_MAP.get(event_dict["Flagged Severity"], "#64748B")
        cumulative_events.append(event_dict)
        accumulated_logs.append(event_dict["Log_Line"])

    danger_score = current_step_meta["danger_score"]
    status_label, bg_color, accent_color = _get_danger_meta(danger_score)

    events_df = pd.DataFrame(cumulative_events)

    return {
        "scenario": scenario_name,
        "step_index": step_idx,
        "max_steps": len(raw_steps),
        "stage_title": current_step_meta["stage_title"],
        "danger_score": danger_score,
        "danger_status": status_label,
        "danger_bg_color": bg_color,
        "danger_accent_color": accent_color,
        "timeline_events": cumulative_events,
        "events_df": events_df,
        "story": current_step_meta["story"],
        "logs": accumulated_logs,
    }


def get_all_forensic_data() -> pd.DataFrame:
    """Return complete synthetic dataset across all scenarios for detailed forensic investigation."""
    all_events: List[Dict[str, Any]] = []

    for step in ATTACK_STEPS:
        ev = dict(step["new_event"])
        ev["Scenario"] = SCENARIO_ATTACK
        all_events.append(ev)

    for step in NORMAL_STEPS:
        ev = dict(step["new_event"])
        ev["Scenario"] = SCENARIO_NORMAL
        all_events.append(ev)

    # Add extra background baseline traffic for forensic filtering realism
    background_logs = [
        {
            "Timestamp": "2026-10-29 01:10:04",
            "time_seq": "01:10:04",
            "User": "alex.turner@acme-corp.com",
            "Action": "Teams Messaging Thread Joined",
            "IP Address": "64.124.8.19",
            "Device": "Dell XPS 15 / Windows 11 Enterprise",
            "Country": "United States",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[01:10:04] INFO [TEAMS] Alex Turner connected to internal channel #general.",
            "Scenario": SCENARIO_NORMAL,
        },
        {
            "Timestamp": "2026-10-29 02:05:18",
            "time_seq": "02:05:18",
            "User": "billing-bot@acme-corp.com",
            "Action": "Stripe Webhook Sync",
            "IP Address": "54.187.205.12",
            "Device": "AWS us-west-2 Lambda",
            "Country": "United States",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[02:05:18] INFO [BILLING] Webhook event evt_3Nk98 validated with Stripe signature.",
            "Scenario": SCENARIO_NORMAL,
        },
        {
            "Timestamp": "2026-10-29 02:30:14",
            "time_seq": "02:30:14",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Password Reset Token Requested",
            "IP Address": "185.220.101.44",
            "Device": "Tor Exit Node (Unknown Browser)",
            "Country": "Netherlands",
            "Flagged Severity": "Medium",
            "is_suspicious": True,
            "Log_Line": "[02:30:14] WARN [AUTH_SERVICE] Automated password reset requested for 'sarah.chen@acme-corp.com'. Token suppressed by rate limiter.",
            "Scenario": SCENARIO_ATTACK,
        },
        {
            "Timestamp": "2026-10-29 03:15:22",
            "time_seq": "03:15:22",
            "User": "sarah.chen@acme-corp.com",
            "Action": "Outlook Web Access Rule Enumeration",
            "IP Address": "94.25.182.11",
            "Device": "Linux x86_64 / Chrome 128",
            "Country": "Russia",
            "Flagged Severity": "High",
            "is_suspicious": True,
            "Log_Line": "[03:15:22] WARN [EXCHANGE_ONLINE] Get-InboxRule cmdlet executed from untrusted geo 94.25.182.11.",
            "Scenario": SCENARIO_ATTACK,
        },
        {
            "Timestamp": "2026-10-29 04:00:11",
            "time_seq": "04:00:11",
            "User": "security-orchestrator@acme-corp.com",
            "Action": "Automated Response Rule Invoked",
            "IP Address": "127.0.0.1",
            "Device": "CyberPulse SOAR Agent",
            "Country": "Internal",
            "Flagged Severity": "Info",
            "is_suspicious": False,
            "Log_Line": "[04:00:11] INFO [CYBERPULSE] SOC alert correlation bundle #CP-2026-992 compiled.",
            "Scenario": SCENARIO_ATTACK,
        },
    ]

    all_events.extend(background_logs)
    df = pd.DataFrame(all_events)
    # Sort chronologically
    df["dt_sort"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values("dt_sort", ascending=False).drop(columns=["dt_sort"])
    return df
