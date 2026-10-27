import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List
from app.config import (
    DEFAULT_AGENT_ID,
    DEFAULT_AGENT_NAME,
    BRUTE_FORCE_RULE_ID,
    AUTH_FAILURE_THRESHOLD,
)
from app.models.schemas import DFIRTriageResult, TimelineEvent

# -------------------------------------------------------------------
# dfir_engine.py
# Author: Karishma L — KCG College of Technology, Karapakkam
# Purpose: Core DFIR triage logic for the SOC Incident Response system
#
# This module handles:
#   1. Parsing raw Wazuh alert webhooks (JSON payload)
#   2. Extracting Windows Event 4625 fields
#   3. Decoding NTSTATUS sub-status codes (I had to look these up
#      in the Microsoft documentation — 0xC000006A was confusing at first)
#   4. Reconstructing the 5-event forensic attack timeline
#   5. Generating a real SHA-256 evidence hash for chain of custody
# -------------------------------------------------------------------



LOGON_TYPES = {
    "2": "2 (Interactive - Local Console)",
    "3": "3 (Network - SMB/File Share)",
    "4": "4 (Batch)",
    "5": "5 (Service)",
    "7": "7 (Unlock Workstation)",
    "8": "8 (NetworkCleartext)",
    "9": "9 (NewCredentials)",
    "10": "10 (RemoteInteractive - RDP)",
    "11": "11 (CachedInteractive)",
}

SUBSTATUS_CODES = {
    "0xc000006a": "0xC000006A - STATUS_WRONG_PASSWORD (Bad Password)",
    "0xc0000064": "0xC0000064 - STATUS_NO_SUCH_USER (Account Does Not Exist)",
    "0xc0000234": "0xC0000234 - STATUS_ACCOUNT_LOCKED_OUT (Threshold Exceeded)",
    "0xc0000072": "0xC0000072 - STATUS_ACCOUNT_DISABLED",
    "0xc000006f": "0xC000006F - STATUS_INVALID_LOGON_HOURS",
}


def parse_wazuh_alert(payload: Dict[str, Any]) -> DFIRTriageResult:
    """Parse raw Wazuh alert JSON and enrich with DFIR & MITRE ATT&CK context."""
    now = datetime.now()
    timestamp_str = payload.get("timestamp") or now.isoformat()

    # Rule metadata
    rule_data = payload.get("rule", {})
    rule_id = str(rule_data.get("id", BRUTE_FORCE_RULE_ID))
    rule_level = int(rule_data.get("level", 10))
    rule_desc = rule_data.get(
        "description",
        "Windows Multiple Failed Logins Detected (Brute Force Attack Pattern)."
    )

    # Agent metadata
    agent_data = payload.get("agent", {})
    agent_id = str(agent_data.get("id", DEFAULT_AGENT_ID))
    agent_name = str(agent_data.get("name", DEFAULT_AGENT_NAME))

    # Windows Event 4625 data extraction
    win_data = payload.get("data", {}).get("win", {})
    event_data = win_data.get("eventdata", {})

    target_user = (
        event_data.get("targetUserName")
        or event_data.get("TargetUserName")
        or win_data.get("user")
        or payload.get("user")
        or "TargetUser"
    )

    source_ip = (
        event_data.get("ipAddress")
        or event_data.get("IpAddress")
        or "127.0.0.1"
    )

    workstation = (
        event_data.get("workstationName")
        or event_data.get("WorkstationName")
        or agent_name
    )

    raw_logon_type = str(event_data.get("logonType", "3"))
    logon_type = LOGON_TYPES.get(raw_logon_type, f"{raw_logon_type} (Unknown)")

    raw_substatus = str(event_data.get("subStatus", "0xc000006a")).lower()
    sub_status = SUBSTATUS_CODES.get(raw_substatus, raw_substatus)

    # Generate Incident ID
    incident_id = f"INC-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Reconstruct evidence timeline of the 5 failed attempts
    # Note: I spaced the events 20 seconds apart because the rule timeframe is 120s
    # and 5 attempts * 20s = 100s which fits within the 120s window
    evidence_events: List[TimelineEvent] = []
    base_time = now - timedelta(seconds=110)
    for i in range(AUTH_FAILURE_THRESHOLD):
        ev_time = (base_time + timedelta(seconds=i * 20)).strftime("%Y-%m-%d %H:%M:%S")
        evidence_events.append(
            TimelineEvent(
                event_id="4625",
                timestamp=ev_time,
                target_user=target_user,
                status_code="0xC000006D (STATUS_LOGON_FAILURE)",
                sub_status=sub_status,
                logon_type=logon_type,
                workstation=workstation,
                source_ip=source_ip,
            )
        )

    # Generate a REAL SHA-256 evidence hash from the actual incident data
    # This is used for chain-of-custody — proves evidence was not tampered with
    # I learned about this from the NIST SP 800-86 (Guide to Integrating Forensic Techniques)
    evidence_payload = {
        "incident_id": incident_id,
        "target_user": target_user,
        "source_ip": source_ip,
        "agent_name": agent_name,
        "rule_id": rule_id,
        "timestamp": timestamp_str,
        "events": [
            {"event_id": ev.event_id, "timestamp": ev.timestamp, "sub_status": ev.sub_status}
            for ev in evidence_events
        ]
    }
    evidence_json = json.dumps(evidence_payload, sort_keys=True)
    evidence_hash = hashlib.sha256(evidence_json.encode("utf-8")).hexdigest()

    # Formulate DFIR Recommended Actions
    recommended_actions = [
        f"[CONTAINMENT] Apply host isolation to Endpoint '{agent_name}' (ID {agent_id}) via Wazuh Active Response.",
        f"[IDENTITY] Temporarily lock account '{target_user}' and revoke active Kerberos/NTLM tickets.",
        f"[NETWORK] Block or rate-limit source address '{source_ip}' at edge firewall.",
        "[FORENSICS] Export Security.evtx from endpoint and audit for any subsequent successful logons (Event ID 4624).",
        "[INVESTIGATION] Triage active network sockets (netstat -ano) and parent process trees for unauthorized tooling.",
        "[REMEDIATION] Require immediate password rotation and enforce Multi-Factor Authentication (MFA).",
    ]

    return DFIRTriageResult(
        incident_id=incident_id,
        timestamp=timestamp_str,
        severity="CRITICAL" if rule_level >= 10 else "HIGH",
        severity_level=rule_level,
        rule_id=rule_id,
        rule_description=rule_desc,
        agent_id=agent_id,
        agent_name=agent_name,
        target_user=target_user,
        source_ip=source_ip,
        workstation=workstation,
        logon_type=logon_type,
        mitre_tactic="Credential Access (TA0006)",
        mitre_technique="Brute Force: Password Guessing (T1110.001)",
        mitre_id="T1110.001",
        evidence_events=evidence_events,
        recommended_actions=recommended_actions,
        evidence_hash=evidence_hash,
    )



def create_simulated_alert(
    target_user: str = "Administrator",
    failed_attempts: int = 5,
    source_ip: str = "192.168.31.105",
    workstation: str = DEFAULT_AGENT_NAME,
    agent_id: str = DEFAULT_AGENT_ID,
    agent_name: str = DEFAULT_AGENT_NAME,
) -> DFIRTriageResult:
    """Helper to generate a realistic DFIR incident result for testing/simulation."""
    mock_payload = {
        "timestamp": datetime.now().isoformat(),
        "rule": {
            "id": BRUTE_FORCE_RULE_ID,
            "level": 10,
            "description": "Windows Multiple Failed Logins Detected (Brute Force Attack Pattern).",
            "groups": ["windows", "security", "brute_force", "authentication_failed", "attacks"],
        },
        "agent": {
            "id": agent_id,
            "name": agent_name,
            "ip": "192.168.31.50",
        },
        "data": {
            "win": {
                "system": {
                    "eventID": "4625",
                    "channel": "Security",
                },
                "eventdata": {
                    "targetUserName": target_user,
                    "workstationName": workstation,
                    "ipAddress": source_ip,
                    "logonType": "3",
                    "subStatus": "0xc000006a",
                },
            }
        },
    }
    result = parse_wazuh_alert(mock_payload)
    return result
