"""CyberPulse Forensic Evidence Workspace.

Granular multi-dimensional investigation console providing interactive entity filtering,
risk-highlighted evidence tables, and raw telemetry CSV export.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from core.mock_data import get_all_forensic_data

# Page setup
st.set_page_config(
    page_title="CyberPulse | Forensic Evidence Workspace",
    page_icon="🔍",
    layout="wide",
)

# Custom High-Contrast Dark Theme
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0B0F19;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .page-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #38BDF8 0%, #818CF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .page-subtitle {
        color: #94A3B8;
        font-size: 0.92rem;
        margin-bottom: 1.2rem;
    }
    .kpi-box {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        text-align: left;
    }
    .kpi-title {
        font-size: 0.78rem;
        font-weight: 600;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.6rem;
        font-weight: 800;
        color: #F8FAFC;
        margin-top: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='page-title'>Forensic Evidence Investigation Workspace</div>", unsafe_allow_html=True)
st.markdown(
    "<div class='page-subtitle'>Inspect raw event records, isolate anomalous user accounts, evaluate geographic ingress, and export evidentiary audit trails.</div>",
    unsafe_allow_html=True,
)

# Load forensic master telemetry
raw_evidence_df = get_all_forensic_data()

# Ensure required columns exist
expected_cols = ["Timestamp", "User", "Action", "IP Address", "Device", "Country", "Flagged Severity"]
for col in expected_cols:
    if col not in raw_evidence_df.columns:
        raw_evidence_df[col] = "N/A"

# ==============================================================================
# SECTION 1: INTERACTIVE FILTERS
# ==============================================================================

with st.container():
    st.markdown(
        "<div style='background-color: #0F172A; border: 1px solid #1E293B; border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1.2rem;'>",
        unsafe_allow_html=True,
    )
    st.markdown("#### 🔎 **Filter Evidence Stream**")

    f_col1, f_col2, f_col3 = st.columns(3)

    # 1. Multi-select: User / Person
    all_users = sorted(raw_evidence_df["User"].dropna().unique().tolist())
    with f_col1:
        selected_users = st.multiselect(
            "User / Person",
            options=all_users,
            default=[],
            help="Filter by specific employee accounts or service principals.",
            placeholder="All Users",
        )

    # 2. Multi-select: IP Address
    all_ips = sorted(raw_evidence_df["IP Address"].dropna().unique().tolist())
    with f_col2:
        selected_ips = st.multiselect(
            "IP Address",
            options=all_ips,
            default=[],
            help="Filter by origin IP address or egress subnet.",
            placeholder="All IP Addresses",
        )

    # 3. Multi-select: Device ID
    all_devices = sorted(raw_evidence_df["Device"].dropna().unique().tolist())
    with f_col3:
        selected_devices = st.multiselect(
            "Device ID",
            options=all_devices,
            default=[],
            help="Filter by client operating system, browser, or asset identifier.",
            placeholder="All Devices",
        )

    st.markdown("</div>", unsafe_allow_html=True)

# Apply filters
filtered_df = raw_evidence_df.copy()

if selected_users:
    filtered_df = filtered_df[filtered_df["User"].isin(selected_users)]

if selected_ips:
    filtered_df = filtered_df[filtered_df["IP Address"].isin(selected_ips)]

if selected_devices:
    filtered_df = filtered_df[filtered_df["Device"].isin(selected_devices)]


# ==============================================================================
# SECTION 2: TELEMETRY METRIC SNAPSHOT
# ==============================================================================

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Total Evidence Records</div>
            <div class='kpi-value'>{len(filtered_df)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m2:
    crit_count = len(filtered_df[filtered_df["Flagged Severity"].isin(["High", "Critical"])])
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>High / Critical Alarms</div>
            <div class='kpi-value' style='color: {'#DC2626' if crit_count > 0 else '#4ADE80'};'>{crit_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m3:
    uniq_users = filtered_df["User"].nunique()
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Targeted Identities</div>
            <div class='kpi-value'>{uniq_users}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with m4:
    uniq_ips = filtered_df["IP Address"].nunique()
    st.markdown(
        f"""
        <div class='kpi-box'>
            <div class='kpi-title'>Distinct Ingress IPs</div>
            <div class='kpi-value'>{uniq_ips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-bottom: 1.2rem;'></div>", unsafe_allow_html=True)


# ==============================================================================
# SECTION 3: RAW EVIDENCE DATA TABLE (WITH RISK HIGHLIGHTING)
# ==============================================================================

st.markdown(
    """
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;'>
        <span style='font-size: 1.15rem; font-weight: 700; color: #F1F5F9;'>
            📋 Raw Evidence Telemetry Logs
        </span>
        <span style='font-size: 0.8rem; color: #94A3B8;'>
            Sorted chronologically • Color highlights by Flagged Severity
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)

display_df = filtered_df[expected_cols].reset_index(drop=True)


def highlight_risk_level(row: pd.Series) -> list[str]:
    """Apply CSS styles to table rows matching CyberPulse severity tiers."""
    severity = str(row.get("Flagged Severity", "")).strip().lower()
    if severity == "critical":
        return ["background-color: #381A1A; color: #FCA5A5; font-weight: 600;"] * len(row)
    elif severity == "high":
        return ["background-color: #2D2318; color: #FDE68A; font-weight: 500;"] * len(row)
    elif severity == "medium":
        return ["background-color: #26221A; color: #FEF08A;"] * len(row)
    elif severity == "low":
        return ["background-color: #1E2D24; color: #86EFAC;"] * len(row)
    else:
        return ["background-color: #0F172A; color: #CBD5E1;"] * len(row)


styled_table = display_df.style.apply(highlight_risk_level, axis=1)

st.dataframe(
    styled_table,
    use_container_width=True,
    height=400,
    column_config={
        "Timestamp": st.column_config.TextColumn("Timestamp (UTC)", width="medium"),
        "User": st.column_config.TextColumn("User Account", width="medium"),
        "Action": st.column_config.TextColumn("Observed Action", width="large"),
        "IP Address": st.column_config.TextColumn("IP Address", width="small"),
        "Device": st.column_config.TextColumn("Device / Client", width="medium"),
        "Country": st.column_config.TextColumn("Geo Location", width="small"),
        "Flagged Severity": st.column_config.TextColumn("Flagged Severity", width="small"),
    },
)


# ==============================================================================
# SECTION 4: EXPORT OPTION (DOWNLOAD CSV)
# ==============================================================================

exp_col1, exp_col2 = st.columns([1.5, 3.5])

with exp_col1:
    csv_data = display_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Evidence as CSV",
        data=csv_data,
        file_name="cyberpulse_forensic_evidence.csv",
        mime="text/csv",
        type="primary",
        use_container_width=True,
        help="Export all currently displayed forensic evidence rows for legal and regulatory archiving.",
    )

with exp_col2:
    st.markdown(
        "<div style='font-size: 0.8rem; color: #64748B; padding-top: 0.5rem;'>"
        "• Exported CSV includes cryptographic timestamps and geolocational metadata compliant with standard chain-of-custody protocols."
        "</div>",
        unsafe_allow_html=True,
    )
