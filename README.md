# CyberPulse 🛡️
**Early-Warning Cyber Incident Response Platform — for Small Businesses**

A production-ready Streamlit SOC dashboard with embedded mock scenario engine, autonomous playback simulation, and one-click mitigation actions — all fully offline with zero backend dependency.

---

## Project Structure

```
CyberPulse/
├── app.py                    ← SOC Dashboard (main entry point)
├── pages/
│   ├── 1_Incident_Details.py ← Forensic Evidence Investigation Workspace
│   └── 2_Scorecard.py        ← Executive KPI Scorecard (Harish's Benchmarks)
├── core/
│   ├── __init__.py
│   ├── mock_data.py          ← Self-contained mock attack & normal day engine
│   └── response.py           ← Mitigation action state manager
├── .streamlit/
│   └── config.toml           ← Dark theme configuration
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Create virtual environment
```bash
python -m venv .venv
```

### 2. Install dependencies
```bash
# With uv (faster)
uv pip install -r requirements.txt --python .venv/Scripts/python.exe

# Or with pip
.venv\Scripts\pip install -r requirements.txt
```

### 3. Run the app
```bash
.venv\Scripts\streamlit run app.py
```

Or use the included launcher:
```bash
run.bat
```

---

## Features

### `app.py` — SOC Incident Linker Dashboard
- 🚨 **Scenario Playback** — Automated step-by-step Attack Takeover simulation with Play/Pause/Next/Reset controls
- 📊 **Danger Meter** — Dynamic 0–100 score with color-shifting container (Green/Amber/Red)
- 🔗 **Attack Timeline** — Plotly horizontal scatter chart linking events chronologically by severity
- 📖 **Plain-English Story** — Keerthana's incident brief: narrative, impact breakdown, recommendations
- 💻 **Live Log Stream** — Color-coded syslog feed highlighting suspicious entries in Amber/Crimson
- ⚡ **Response Quick Panel** — Instant one-click mitigations (`Lock Account`, `Sign Out Sessions`, `Remove Forwarding Rule`) with `@st.fragment` isolation

### `pages/1_Incident_Details.py` — Forensic Evidence Workspace
- 🔎 Multi-select filters: User, IP Address, Device
- 📋 Risk-highlighted evidence table (Crimson/Amber/Green row colouring by severity tier)
- 📥 CSV export for legal chain-of-custody compliance

### `pages/2_Scorecard.py` — Executive Scorecard
- 🎯 Harish's benchmark KPI cards: Attacks Caught, False Alarms, Early Warning Lead Time
- 📑 MITRE ATT&CK-mapped detection breakdown table

---

## Design System

| Token | Hex | Usage |
|---|---|---|
| Slate Blue | `#0F172A` | Primary background |
| Sage Green bg | `#1E2D24` | Watch / low-risk container |
| Sage Green | `#4E8B65` | Safe accent color |
| Amber bg | `#2D2318` | Suspicious container |
| Amber | `#D97706` | Medium threat accent |
| Crimson bg | `#381A1A` | Attack container |
| Crimson | `#DC2626` | Critical threat accent |
| Sky Blue | `#38BDF8` | Primary UI accent / links |

---

## Mock Data Engine

The built-in engine in `core/mock_data.py` provides two complete 5-stage simulations:

**Account Takeover Attack** (danger: 34 → 99)
1. Credential Spray & Brute Force
2. Unauthorized Session from Russia
3. Persistence via Inbox Forwarding Rule
4. Internal Reconnaissance & Privilege Escalation
5. Mass Exfiltration (250 files / 4.2 GB)

**Normal Operating Day** (danger: 8 → 19)
1. Routine MFA Login
2. Document Collaboration
3. Mobile Device Sync
4. Payroll Batch Execution
5. Backup Integrity Verified

---

## Backend Integration

Place your real `core/detection.py` module with the same interface as `core/mock_data.py` — the app automatically detects it and switches from mock to live engine:

```python
# core/detection.py (optional live backend)
def get_scenario_data(scenario_name: str, step_idx: int) -> dict:
    ...
```

---

## MITRE ATT&CK Coverage

| Technique | ID | Detection Vector |
|---|---|---|
| Brute Force | T1110 | Credential spray rate-limit trigger |
| Valid Accounts (stolen) | T1078 | Geo-velocity impossible travel |
| Email Forwarding Rule | T1114.003 | Covert mailbox persistence rule |
| Account Discovery | T1087 | MS Graph high-velocity enumeration |
| Exfiltration Over Web | T1567 | DLP bulk download anomaly |
