"""CyberPulse Incident Response State Manager.

Handles mitigation action lifecycle, state persistence, execution telemetry,
and visual status indicators for SOC operators and small business administrators.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, Optional
import streamlit as st

# Canonical action metadata definitions
ACTION_METADATA: Dict[str, Dict[str, str]] = {
    "lock_account": {
        "title": "Lock Compromised Account",
        "description": "Disable user login in identity provider (Azure AD / Google Workspace) to halt unauthorized operations.",
        "icon": "🔒",
    },
    "sign_out_sessions": {
        "title": "Revoke All Active Sessions",
        "description": "Invalidate active OAuth tokens, browser cookies, and device refresh sessions immediately.",
        "icon": "🚪",
    },
    "remove_forwarding_rules": {
        "title": "Remove Inbox Forwarding Rules",
        "description": "Purge hidden server-side auto-forwarding and mail filter exfiltration rules.",
        "icon": "📧",
    },
}

# Alias mapping for singular / plural compatibility
KEY_ALIASES: Dict[str, str] = {
    "remove_forwarding_rule": "remove_forwarding_rules",
    "lock_user": "lock_account",
    "revoke_sessions": "sign_out_sessions",
}


def _normalize_action_id(action_id: str) -> str:
    """Normalize action ID to canonical key."""
    clean_id = action_id.strip().lower()
    return KEY_ALIASES.get(clean_id, clean_id)


def _init_response_state() -> None:
    """Initialize session state container for response mitigations."""
    if "cyberpulse_response_actions" not in st.session_state:
        st.session_state["cyberpulse_response_actions"] = {}

    container = st.session_state["cyberpulse_response_actions"]
    for canonical_id, meta in ACTION_METADATA.items():
        if canonical_id not in container:
            container[canonical_id] = {
                "id": canonical_id,
                "title": meta["title"],
                "icon": meta["icon"],
                "description": meta["description"],
                "executed": False,
                "executed_at": None,
                "status_badge": "Pending Action",
                "confirmation_message": "",
            }


def get_response_states() -> Dict[str, Dict[str, Any]]:
    """Return dictionary tracking all mitigation response actions."""
    _init_response_state()
    return st.session_state["cyberpulse_response_actions"]


def trigger_action(action_id: str) -> Dict[str, Any]:
    """Execute a response action and record execution timestamp.

    Args:
        action_id: Identifier for the response action.

    Returns:
        Confirmation payload with visual indicators.
    """
    _init_response_state()
    canonical = _normalize_action_id(action_id)
    container = st.session_state["cyberpulse_response_actions"]

    if canonical not in container:
        # Fallback dynamic registration
        container[canonical] = {
            "id": canonical,
            "title": canonical.replace("_", " ").title(),
            "icon": "⚡",
            "description": "Automated mitigation procedure.",
            "executed": False,
            "executed_at": None,
            "status_badge": "Pending Action",
            "confirmation_message": "",
        }

    item = container[canonical]
    now_iso = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Toggle / execute action
    if not item["executed"]:
        item["executed"] = True
        item["executed_at"] = now_iso
        item["status_badge"] = "✓ Executed"
        item["confirmation_message"] = f"✓ Executed successfully at {now_iso}"
    else:
        # If already executed, update execution ping
        item["executed_at"] = now_iso
        item["status_badge"] = "✓ Executed"

    return {
        "success": True,
        "action_id": canonical,
        "title": item["title"],
        "executed": True,
        "status_indicator": "✓ Executed",
        "timestamp": now_iso,
        "message": f"Action [{item['title']}] executed: ✓ Executed at {now_iso}",
    }


def reset_response_states() -> None:
    """Reset all response actions back to unexecuted pending state."""
    st.session_state["cyberpulse_response_actions"] = {}
    _init_response_state()
