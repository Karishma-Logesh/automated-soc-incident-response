from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WazuhRule(BaseModel):
    id: str = "100051"
    level: int = 10
    description: str = "Windows Multiple Failed Logins Detected (Brute Force Attack Pattern)."
    groups: List[str] = Field(default_factory=lambda: ["windows", "security", "brute_force"])


class WazuhAgent(BaseModel):
    id: str = "001"
    name: str = "DESKTOP-BJ2IO2A"
    ip: Optional[str] = "192.168.31.50"


class WazuhAlertPayload(BaseModel):
    timestamp: Optional[str] = None
    rule: Optional[Dict[str, Any]] = None
    agent: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None
    full_log: Optional[str] = None
    location: Optional[str] = None
    manager: Optional[Dict[str, Any]] = None


class TimelineEvent(BaseModel):
    event_id: str = "4625"
    timestamp: str
    target_user: str
    status_code: str = "0xC000006D"
    sub_status: str = "0xC000006A"
    logon_type: str = "3 (Network)"
    workstation: str = "DESKTOP-BJ2IO2A"
    source_ip: str = "127.0.0.1"


class DFIRTriageResult(BaseModel):
    incident_id: str
    timestamp: str
    severity: str = "CRITICAL"
    severity_level: int = 10
    rule_id: str = "100051"
    rule_description: str
    agent_id: str
    agent_name: str
    target_user: str
    source_ip: str
    workstation: str
    logon_type: str
    mitre_tactic: str = "Credential Access (TA0006)"
    mitre_technique: str = "Brute Force: Password Guessing (T1110.001)"
    mitre_id: str = "T1110.001"
    evidence_events: List[TimelineEvent] = Field(default_factory=list)
    recommended_actions: List[str] = Field(default_factory=list)
    evidence_hash: Optional[str] = None
    report_filename: Optional[str] = None
    report_download_url: Optional[str] = None


class SimulationRequest(BaseModel):
    target_user: str = "Administrator"
    failed_attempts: int = 5
    source_ip: str = "192.168.31.105"
    workstation: str = "DESKTOP-BJ2IO2A"
    agent_id: str = "001"
    agent_name: str = "DESKTOP-BJ2IO2A"


# ── New models for upgrade ────────────────────────────────────────────────────

class StatusUpdateRequest(BaseModel):
    status: str  # OPEN | INVESTIGATING | CONTAINED | RESOLVED | CLOSED | FALSE_POSITIVE
    actor: str = "Analyst"


class NoteRequest(BaseModel):
    analyst: str = "Analyst"
    note: str


class ResponseActionRequest(BaseModel):
    action_type: str   # NOTIFY | BLOCK_IP | ISOLATE_HOST | LOCK_ACCOUNT | CUSTOM
    target: str        # IP address, hostname, or account name
    authorized_by: str = "Analyst"
    confirmed: bool = False  # Must be True for disruptive actions
