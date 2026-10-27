"""
app/api/routes.py
All API routes + embedded SOC Dashboard frontend.
Author: Karishma L — KCG College of Technology

API Endpoints:
  POST /api/v1/alerts/webhook              — Ingest Wazuh alert
  POST /api/v1/alerts/simulate             — Simulate brute-force (demo)
  GET  /api/v1/incidents                   — List incidents (filter/search/paginate)
  GET  /api/v1/incidents/{id}              — Incident detail
  PATCH /api/v1/incidents/{id}/status      — Update status
  POST /api/v1/incidents/{id}/notes        — Add investigation note
  GET  /api/v1/incidents/{id}/notes        — Get notes
  GET  /api/v1/incidents/{id}/report       — Download PDF report
  POST /api/v1/incidents/{id}/evidence/collect — Collect DFIR evidence
  GET  /api/v1/incidents/{id}/evidence     — List evidence for incident
  POST /api/v1/evidence/{id}/verify        — Verify SHA-256 of evidence file
  POST /api/v1/incidents/{id}/response     — Execute response action
  GET  /api/v1/incidents/{id}/response     — List response actions
  GET  /api/v1/wazuh/sync                  — Pull real alerts from Wazuh
  GET  /api/v1/wazuh/status                — Wazuh API connection status
  GET  /api/v1/health                      — Backend health check
  GET  /api/v1/stats                       — Dashboard statistics
  GET  /api/v1/audit                       — Audit log
  GET  /                                   — SOC Dashboard frontend
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from app.config import DATA_DIR, REPORTS_DIR, WAZUH_MANAGER_IP
from app.db import (
    add_note, get_audit_log, get_evidence, get_incident,
    get_notes, get_response_actions, get_stats, list_all_evidence,
    list_all_response_actions, list_incidents,
    save_evidence, save_incident, save_response_action,
    update_evidence_verify, update_incident_status, update_response_action,
)
from app.models.schemas import (
    DFIRTriageResult, NoteRequest, ResponseActionRequest,
    SimulationRequest, StatusUpdateRequest,
)
from app.services.dfir_engine import create_simulated_alert, parse_wazuh_alert
from app.services.evidence_collector import collect_all, verify_evidence_hash
from app.services.report_generator import generate_incident_pdf
from app.services.wazuh_client import get_alerts, get_connection_status

router = APIRouter()

# Keep JSON file path for backward-compat (still written for legacy tools)
INCIDENTS_FILE = DATA_DIR / "incidents.json"


# ══════════════════════════════════════════════════════════════════════════════
# ALERT INGESTION
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/api/v1/alerts/webhook", response_model=DFIRTriageResult)
async def receive_wazuh_alert(request: Request):
    """Ingest a live Wazuh alert webhook payload."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    triage = parse_wazuh_alert(payload)
    report_filename = f"{triage.incident_id}_DFIR_Report.pdf"
    pdf_path = REPORTS_DIR / report_filename
    generate_incident_pdf(triage, pdf_path)
    triage.report_filename = report_filename
    triage.report_download_url = f"/api/v1/incidents/{triage.incident_id}/report"

    inc_data = triage.model_dump()
    save_incident(inc_data, data_source="WAZUH_WEBHOOK")
    return triage


@router.post("/api/v1/alerts/simulate", response_model=DFIRTriageResult)
async def simulate_brute_force_alert(body: SimulationRequest):
    """Simulate a Level-10 brute-force alert (clearly labelled SIMULATED)."""
    triage = create_simulated_alert(
        target_user=body.target_user,
        failed_attempts=body.failed_attempts,
        source_ip=body.source_ip,
        workstation=body.workstation,
        agent_id=body.agent_id,
        agent_name=body.agent_name,
    )
    report_filename = f"{triage.incident_id}_DFIR_Report.pdf"
    pdf_path = REPORTS_DIR / report_filename
    generate_incident_pdf(triage, pdf_path)
    triage.report_filename = report_filename
    triage.report_download_url = f"/api/v1/incidents/{triage.incident_id}/report"

    inc_data = triage.model_dump()
    save_incident(inc_data, data_source="SIMULATED")
    return triage


# ══════════════════════════════════════════════════════════════════════════════
# INCIDENT MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/api/v1/incidents")
async def list_incidents_api(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    search: Optional[str] = None,
):
    """List incidents with filtering, search, and pagination."""
    return list_incidents(limit=limit, offset=offset,
                          status=status, severity=severity, search=search)


@router.get("/api/v1/incidents/{incident_id}")
async def get_incident_api(incident_id: str):
    """Full detail of one incident including raw evidence events."""
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    # Attach evidence events from raw_json if available
    if inc.get("_full"):
        inc["evidence_events"] = inc["_full"].get("evidence_events", [])
        inc["recommended_actions"] = inc["_full"].get("recommended_actions", [])
    return inc


@router.patch("/api/v1/incidents/{incident_id}/status")
async def update_status(incident_id: str, body: StatusUpdateRequest):
    """Update incident status (OPEN → INVESTIGATING → CONTAINED → RESOLVED)."""
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    ok = update_incident_status(incident_id, body.status, body.actor)
    if not ok:
        raise HTTPException(status_code=400,
                            detail=f"Invalid status '{body.status}'")
    return {"incident_id": incident_id, "new_status": body.status.upper(), "updated_by": body.actor}


# ══════════════════════════════════════════════════════════════════════════════
# INVESTIGATION NOTES
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/api/v1/incidents/{incident_id}/notes")
async def add_note_api(incident_id: str, body: NoteRequest):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    if not body.note.strip():
        raise HTTPException(status_code=400, detail="Note cannot be empty")
    note_id = add_note(incident_id, body.analyst, body.note.strip())
    return {"note_id": note_id, "incident_id": incident_id, "analyst": body.analyst}


@router.get("/api/v1/incidents/{incident_id}/notes")
async def get_notes_api(incident_id: str):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_notes(incident_id)


# ══════════════════════════════════════════════════════════════════════════════
# PDF REPORT
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/api/v1/incidents/{incident_id}/report")
async def download_report(incident_id: str):
    pdf_path = REPORTS_DIR / f"{incident_id}_DFIR_Report.pdf"
    if not pdf_path.exists():
        inc = get_incident(incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="Incident not found")
        full = inc.get("_full", inc)
        try:
            triage = DFIRTriageResult(**full)
            generate_incident_pdf(triage, pdf_path)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    return FileResponse(str(pdf_path), media_type="application/pdf",
                        filename=f"{incident_id}_DFIR_Report.pdf")


# ══════════════════════════════════════════════════════════════════════════════
# DFIR EVIDENCE COLLECTION
# ══════════════════════════════════════════════════════════════════════════════

@router.post("/api/v1/incidents/{incident_id}/evidence/collect")
async def collect_evidence(incident_id: str):
    """
    Collect DFIR artifacts for an incident.
    Runs real OS commands — records honest failures.
    """
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    results = collect_all(incident_id)
    saved = []
    for r in results:
        eid = save_evidence(
            incident_id=incident_id,
            artifact_type=r["artifact_type"],
            filename=r["filename"],
            filepath=r["filepath"],
            sha256=r.get("sha256_hash"),
            result=r["result"],
            error=r.get("error"),
        )
        r["evidence_id"] = eid
        saved.append(r)

    return {
        "incident_id": incident_id,
        "artifacts_attempted": len(saved),
        "artifacts_succeeded": sum(1 for r in saved if r["result"] == "SUCCESS"),
        "results": saved,
    }


@router.get("/api/v1/evidence")
async def list_all_evidence_api(limit: int = Query(100, ge=1, le=500)):
    """List all DFIR forensic evidence records across incidents."""
    return list_all_evidence(limit=limit)


@router.get("/api/v1/incidents/{incident_id}/evidence")
async def list_evidence(incident_id: str):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_evidence(incident_id)


@router.post("/api/v1/evidence/{evidence_id}/verify")
async def verify_evidence(evidence_id: int):
    """Recalculate SHA-256 and compare with stored hash."""
    conn_ev = get_evidence_by_id(evidence_id)
    if not conn_ev:
        raise HTTPException(status_code=404, detail="Evidence record not found")
    result = verify_evidence_hash(conn_ev["filepath"], conn_ev["sha256_hash"] or "")
    update_evidence_verify(evidence_id, result["result"])
    return result


def get_evidence_by_id(evidence_id: int) -> Optional[Dict]:
    from app.db import get_conn
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM evidence_records WHERE id=?", (evidence_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# ══════════════════════════════════════════════════════════════════════════════
# RESPONSE ACTIONS
# ══════════════════════════════════════════════════════════════════════════════

SAFE_ACTIONS = {"NOTIFY", "TAG_INCIDENT"}
DISRUPTIVE_ACTIONS = {"BLOCK_IP", "LOCK_ACCOUNT", "ISOLATE_HOST"}


@router.post("/api/v1/incidents/{incident_id}/response")
async def create_response_action(incident_id: str, body: ResponseActionRequest):
    """
    Execute a controlled response action.
    Disruptive actions require confirmed=True.
    Actual execution is logged honestly — no fabricated results.
    """
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")

    action = body.action_type.upper()
    if action in DISRUPTIVE_ACTIONS and not body.confirmed:
        raise HTTPException(
            status_code=400,
            detail=f"Action '{action}' is disruptive and requires confirmed=true"
        )

    aid = save_response_action(incident_id, action, body.target, body.authorized_by)

    # Execute the action
    result, status = _execute_action(action, body.target, incident_id)
    update_response_action(aid, status, result)

    return {
        "action_id": aid,
        "incident_id": incident_id,
        "action_type": action,
        "target": body.target,
        "status": status,
        "result": result,
        "executed_at": datetime.now().isoformat(),
    }


def _execute_action(action: str, target: str, incident_id: str):
    """
    Execute response actions.
    Safe actions are executed directly.
    Disruptive actions require Wazuh Active Response — reported honestly if unavailable.
    """
    if action == "NOTIFY":
        return f"Incident {incident_id} flagged for analyst review. Target: {target}", "COMPLETED"

    if action == "TAG_INCIDENT":
        return f"Incident tagged with: {target}", "COMPLETED"

    if action == "BLOCK_IP":
        # Would require Wazuh Active Response or firewall API — not available without config
        return (
            "BLOCKED via Wazuh Active Response: NOT EXECUTED. "
            "Wazuh active-response.conf firewall-drop command must be configured on the manager. "
            f"Manual action required: Block {target} at edge firewall.",
            "MANUAL_REQUIRED"
        )

    if action == "LOCK_ACCOUNT":
        return (
            f"ACCOUNT LOCK: NOT EXECUTED. "
            f"Active Directory API or net user command required to lock '{target}'. "
            "Manual action required: Run 'net user {target} /active:no' on Domain Controller.",
            "MANUAL_REQUIRED"
        )

    if action == "ISOLATE_HOST":
        return (
            f"HOST ISOLATION: NOT EXECUTED. "
            f"Wazuh Active Response 'route-null' command must be configured on agent {target}. "
            "Verify wazuh-agent active-response is enabled before claiming isolation.",
            "MANUAL_REQUIRED"
        )

    return f"Unknown action: {action}", "FAILED"


@router.get("/api/v1/response")
async def list_all_response_actions_api(limit: int = Query(100, ge=1, le=500)):
    """List all response actions across incidents."""
    return list_all_response_actions(limit=limit)


@router.get("/api/v1/incidents/{incident_id}/response")
async def list_response_actions(incident_id: str):
    inc = get_incident(incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail="Incident not found")
    return get_response_actions(incident_id)


# ══════════════════════════════════════════════════════════════════════════════
# WAZUH INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/api/v1/wazuh/status")
async def wazuh_status():
    """Real Wazuh API connection status — never fabricated."""
    return get_connection_status()


@router.get("/api/v1/wazuh/sync")
async def wazuh_sync():
    """
    Pull real alerts from Wazuh API and save new ones as incidents.
    Deduplicates by alert ID.
    """
    status = get_connection_status()
    if not status["connected"]:
        return {
            "synced": False,
            "message": status["message"],
            "wazuh_status": status["status"],
            "new_incidents": 0,
        }

    ok, alerts_or_err = get_alerts(limit=50, rule_level_gte=7)
    if not ok:
        return {
            "synced": False,
            "message": str(alerts_or_err),
            "new_incidents": 0,
        }

    new_count = 0
    for alert in (alerts_or_err or []):
        # Use Wazuh alert ID as dedup key — stored in incident_id
        alert_id = alert.get("id", "")
        if not alert_id:
            continue

        # Check if already exists
        existing = get_incident(f"WAZ-{alert_id[:20]}")
        if existing:
            continue

        try:
            triage = parse_wazuh_alert(alert)
            triage.incident_id = f"WAZ-{alert_id[:20]}"
            report_filename = f"{triage.incident_id}_DFIR_Report.pdf"
            pdf_path = REPORTS_DIR / report_filename
            generate_incident_pdf(triage, pdf_path)
            triage.report_filename = report_filename
            triage.report_download_url = f"/api/v1/incidents/{triage.incident_id}/report"
            save_incident(triage.model_dump(), data_source="WAZUH_SYNC")
            new_count += 1
        except Exception as e:
            continue

    return {
        "synced": True,
        "alerts_retrieved": len(alerts_or_err),
        "new_incidents": new_count,
        "synced_at": datetime.now().isoformat(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# HEALTH, STATS, AUDIT
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/api/v1/health")
async def health_check():
    """Backend health and integration status."""
    from app.db import DB_PATH
    db_ok = DB_PATH.exists()
    wazuh = get_connection_status()
    return {
        "status": "OK",
        "version": "2.0.0",
        "database": "OK" if db_ok else "MISSING",
        "db_path": str(DB_PATH),
        "wazuh_connected": wazuh["connected"],
        "wazuh_status": wazuh["status"],
        "reports_dir": str(REPORTS_DIR),
        "checked_at": datetime.now().isoformat(),
    }


@router.get("/api/v1/stats")
async def get_statistics():
    """Real database statistics — no hardcoded numbers."""
    return get_stats()


@router.get("/api/v1/audit")
async def get_audit(
    limit: int = Query(100, ge=1, le=1000),
    incident_id: Optional[str] = None,
):
    return get_audit_log(limit=limit, incident_id=incident_id)


# ══════════════════════════════════════════════════════════════════════════════
# FRONTEND — Multi-page SOC Dashboard
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=_build_dashboard_html())


def _build_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOC Incident Response Platform — KCG College of Technology</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg:             #F1F3F5;
    --surface:        #FFFFFF;
    --surface-hover:  #F8F9FA;
    --sidebar-bg:     #263746;
    --sidebar-hover:  #324659;
    --sidebar-active: #1D2A36;
    --border:         #D9DEE5;
    --border-light:   #E9ECEF;
    --text:           #252B32;
    --muted:          #697586;
    --bright:         #1A2027;
    --blue:           #477B9E;
    --blue-dark:      #36607C;
    --red:            #B64040;
    --orange:         #C58A32;
    --green:          #39816C;
    --mono:           'JetBrains Mono', 'Consolas', monospace;
  }
  html, body {
    height: 100%;
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
    letter-spacing: -0.01em;
  }
  a { color: var(--blue); text-decoration: none; }

  /* Layout */
  #app { display: flex; height: 100vh; overflow: hidden; }
  #sidebar {
    width: 210px; flex-shrink: 0;
    background: var(--sidebar-bg);
    border-right: 1px solid #1E2D3A;
    display: flex; flex-direction: column;
    overflow-y: auto;
  }
  #main { flex: 1; display: flex; flex-direction: column; overflow: hidden; background: var(--bg); }
  #topbar {
    height: 48px; flex-shrink: 0;
    background: #FFFFFF;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center;
    padding: 0 20px; gap: 14px;
  }
  #content { flex: 1; overflow-y: auto; padding: 20px; background: var(--bg); }

  /* Sidebar */
  .sidebar-logo {
    padding: 14px 16px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 12px; font-weight: 700; color: #FFFFFF;
    line-height: 1.4;
  }
  .sidebar-logo small { display: block; color: #9AA8B6; font-weight: 400; font-size: 10px; margin-top: 2px; }
  .nav-section { padding: 10px 0 4px; }
  .nav-label { padding: 4px 16px; font-size: 10px; font-weight: 600; color: #7F93A5; text-transform: uppercase; letter-spacing: 0.8px; }
  .nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 8px 16px; cursor: pointer;
    color: #CBD5E1; font-size: 12px; font-weight: 500;
    border-left: 3px solid transparent;
    transition: all 0.15s ease;
  }
  .nav-item:hover { color: #FFFFFF; background: var(--sidebar-hover); }
  .nav-item.active {
    color: #FFFFFF;
    border-left-color: var(--blue);
    background: var(--sidebar-active);
    font-weight: 600;
  }
  .nav-item i { width: 14px; text-align: center; font-size: 12px; opacity: 0.85; }

  /* Topbar */
  .topbar-title { font-size: 14px; font-weight: 600; color: var(--bright); flex: 1; letter-spacing: -0.01em; }
  .wazuh-status {
    display: flex; align-items: center; gap: 7px;
    font-size: 11px; font-family: var(--mono);
    padding: 4px 10px; background: #F8F9FA;
    border: 1px solid var(--border); border-radius: 4px;
    font-weight: 500;
  }
  .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); }
  .dot.ok { background: var(--green); }
  .dot.err { background: var(--red); }
  .dot.warn { background: var(--orange); }
  .btn {
    padding: 6px 12px; border: 1px solid transparent; border-radius: 4px;
    font-size: 12px; font-weight: 600; cursor: pointer; transition: all 0.15s ease;
  }
  .btn:hover { opacity: 0.92; }
  .btn-primary { background: var(--blue); color: #FFFFFF; border-color: var(--blue-dark); }
  .btn-primary:hover { background: var(--blue-dark); }
  .btn-danger  { background: var(--red); color: #FFFFFF; border-color: #9E3535; }
  .btn-danger:hover { background: #A03434; }
  .btn-outline {
    background: #FFFFFF; color: var(--text);
    border: 1px solid var(--border);
  }
  .btn-outline:hover { background: #F8F9FA; color: var(--bright); border-color: #BCC5CE; }
  .btn-sm { padding: 4px 10px; font-size: 11px; }

  /* Page sections */
  .page { display: none; }
  .page.active { display: block; }
  .page-header { margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }
  .page-title { font-size: 16px; font-weight: 700; color: var(--bright); letter-spacing: -0.01em; }
  .page-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }

  /* Cards / panels */
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 4px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    overflow: hidden;
  }
  .panel-head {
    padding: 11px 16px;
    background: #FAFBFC;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    font-size: 12px; font-weight: 600; color: var(--bright);
  }
  .panel-body { padding: 16px; background: var(--surface); }

  /* Stat cards */
  .stat-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 16px; }
  .stat-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 4px; padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  }
  .stat-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; font-weight: 600; margin-bottom: 6px; }
  .stat-value { font-size: 24px; font-weight: 700; color: var(--bright); font-family: var(--mono); }
  .stat-sub { font-size: 11px; color: var(--muted); margin-top: 4px; }

  /* Tables */
  .data-table { width: 100%; border-collapse: collapse; background: var(--surface); }
  .data-table th {
    padding: 10px 12px; text-align: left;
    font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.6px;
    color: var(--muted); background: #F8F9FA;
    border-bottom: 1px solid var(--border);
  }
  .data-table td {
    padding: 10px 12px;
    font-size: 12px; color: var(--text);
    border-bottom: 1px solid var(--border-light);
    vertical-align: middle;
  }
  .data-table tr:hover td { background: #F8F9FA; }
  .data-table .mono-cell { font-family: var(--mono); font-size: 11px; }

  /* Badges */
  .badge {
    display: inline-flex; align-items: center; gap: 4px; padding: 3px 8px; border-radius: 3px;
    font-size: 10px; font-weight: 600; font-family: var(--mono);
    text-transform: uppercase; letter-spacing: 0.4px;
  }
  .badge-red    { background: #FDE8E8; color: var(--red); border: 1px solid #F8B4B4; }
  .badge-orange { background: #FEF3C7; color: var(--orange); border: 1px solid #FCD34D; }
  .badge-green  { background: #DEF7EC; color: var(--green); border: 1px solid #BCF0DA; }
  .badge-blue   { background: #E1EFFE; color: var(--blue); border: 1px solid #B4C6E7; }
  .badge-muted  { background: #F3F4F6; color: var(--muted); border: 1px solid var(--border); }

  /* Source label */
  .src-real { color: var(--green); font-family: var(--mono); font-size: 10px; font-weight: 600; }
  .src-sim  { color: var(--muted); font-family: var(--mono); font-size: 10px; }

  /* Filter bar */
  .filter-bar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap; }
  .filter-bar input, .filter-bar select {
    background: #FFFFFF; border: 1px solid var(--border);
    color: var(--text); padding: 6px 10px; border-radius: 4px;
    font-size: 12px; font-family: inherit;
  }
  .filter-bar input:focus, .filter-bar select:focus { outline: none; border-color: var(--blue); }

  /* Detail panel */
  .detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .kv-block { margin-bottom: 8px; }
  .kv-label { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; font-weight: 600; }
  .kv-value { font-size: 12px; color: var(--bright); font-family: var(--mono); }

  /* Notes */
  .note-entry {
    padding: 8px 12px; border-left: 3px solid var(--blue);
    background: #F8F9FA; margin-bottom: 8px;
    border-radius: 0 4px 4px 0; border-top: 1px solid var(--border-light);
    border-right: 1px solid var(--border-light); border-bottom: 1px solid var(--border-light);
  }
  .note-meta { font-size: 10px; color: var(--muted); margin-bottom: 3px; font-weight: 500; }
  .note-text { font-size: 12px; color: var(--text); }
  textarea.note-input {
    width: 100%; background: #FFFFFF; border: 1px solid var(--border);
    color: var(--text); padding: 8px; border-radius: 4px;
    font-family: inherit; font-size: 12px; resize: vertical; min-height: 60px;
  }
  textarea.note-input:focus { outline: none; border-color: var(--blue); }

  /* Evidence */
  .hash-cell { font-family: var(--mono); font-size: 10px; word-break: break-all; color: var(--bright); }

  /* Alert banner */
  .alert-banner {
    display: none;
    padding: 10px 16px; margin-bottom: 14px;
    background: #FDE8E8; border: 1px solid #F8B4B4;
    border-radius: 4px; font-size: 12px; color: var(--red);
    display: flex; align-items: center; gap: 8px;
  }

  /* Emergency strobe */
  #strobe { display: none; position: fixed; inset: 0; pointer-events: none; z-index: 9999; }
  @keyframes strobe {
    0%,100% { background: rgba(182, 64, 64, 0.15); }
    50%      { background: rgba(182, 64, 64, 0.03); }
  }
  .strobe-on { display: block !important; animation: strobe 0.7s infinite; }

  /* Incident count badge in nav */
  .nav-badge {
    margin-left: auto; background: var(--red);
    color: #FFFFFF; border-radius: 3px; font-size: 10px;
    padding: 1px 6px; font-weight: 700; font-family: var(--mono);
  }

  /* Toast */
  #toast {
    position: fixed; bottom: 16px; right: 16px;
    background: #FFFFFF; border: 1px solid var(--border);
    color: var(--text); padding: 10px 16px; border-radius: 4px;
    font-size: 12px; display: none; z-index: 10000;
    max-width: 360px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  }
  .loading { color: var(--muted); padding: 24px; text-align: center; font-size: 12px; }
  .empty { color: var(--muted); padding: 24px; text-align: center; font-size: 12px; }

  /* Pagination */
  .pagination { display: flex; gap: 4px; align-items: center; margin-top: 10px; }
  .page-btn {
    padding: 3px 8px; border: 1px solid var(--border);
    background: #FFFFFF; color: var(--text);
    border-radius: 3px; font-size: 11px; cursor: pointer;
  }
  .page-btn.active { background: var(--blue); border-color: var(--blue); color: #fff; }
  .page-btn:disabled { opacity: 0.4; cursor: not-allowed; }

  /* Health grid */
  .health-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .health-row { display: flex; justify-content: space-between; align-items: flex-start; padding: 8px 0; border-bottom: 1px solid var(--border-light); font-size: 12px; gap: 12px; }
  .health-row:last-child { border-bottom: none; }
  .health-key { color: var(--muted); flex-shrink: 0; font-weight: 500; }
  .health-val { color: var(--bright); font-family: var(--mono); font-size: 11px; word-break: break-all; text-align: right; }

  /* Chart container */
  .chart-wrap { position: relative; height: 160px; }

  /* Responsive */
  @media (max-width: 900px) {
    #sidebar { width: 40px; }
    .sidebar-logo, .nav-label, .nav-item span { display: none; }
    .nav-item { padding: 10px; justify-content: center; }
    .stat-grid { grid-template-columns: repeat(2, 1fr); }
  }
</style>
</head>
<body>
<div id="strobe"></div>
<div id="toast"></div>

<div id="app">
  <!-- ── SIDEBAR ── -->
  <nav id="sidebar">
    <div class="sidebar-logo">
      SOC Platform
      <small>KCG College of Technology</small>
      <small>Karishma L &bull; B.E. CSE (CS)</small>
    </div>
    <div class="nav-section">
      <div class="nav-label">Operations</div>
      <div class="nav-item active" onclick="showPage('overview')" id="nav-overview">
        <i class="fas fa-chart-line"></i><span>SOC Overview</span>
      </div>
      <div class="nav-item" onclick="showPage('alerts')" id="nav-alerts">
        <i class="fas fa-bell"></i><span>Security Alerts</span>
        <span class="nav-badge" id="open-badge" style="display:none"></span>
      </div>
      <div class="nav-item" onclick="showPage('incidents')" id="nav-incidents">
        <i class="fas fa-triangle-exclamation"></i><span>Incident Management</span>
      </div>
      <div class="nav-item" onclick="showPage('evidence')" id="nav-evidence">
        <i class="fas fa-microscope"></i><span>DFIR Evidence</span>
      </div>
      <div class="nav-item" onclick="showPage('response')" id="nav-response">
        <i class="fas fa-shield-halved"></i><span>Response Actions</span>
      </div>
    </div>
    <div class="nav-section">
      <div class="nav-label">Reporting</div>
      <div class="nav-item" onclick="showPage('reports')" id="nav-reports">
        <i class="fas fa-file-pdf"></i><span>Reports</span>
      </div>
      <div class="nav-item" onclick="showPage('audit')" id="nav-audit">
        <i class="fas fa-list-check"></i><span>Audit Logs</span>
      </div>
    </div>
    <div class="nav-section">
      <div class="nav-label">System</div>
      <div class="nav-item" onclick="showPage('health')" id="nav-health">
        <i class="fas fa-heartbeat"></i><span>System Health</span>
      </div>
      <div class="nav-item" onclick="showPage('settings')" id="nav-settings">
        <i class="fas fa-gear"></i><span>Settings</span>
      </div>
    </div>
  </nav>

  <!-- ── MAIN ── -->
  <div id="main">
    <!-- Topbar -->
    <div id="topbar">
      <span class="topbar-title" id="topbar-title">SOC Overview</span>
      <div class="wazuh-status">
        <div class="dot" id="wazuh-dot"></div>
        <span id="wazuh-label" style="color:var(--muted)">Wazuh: checking...</span>
      </div>
      <button class="btn btn-outline btn-sm" onclick="syncWazuh()"><i class="fas fa-sync fa-spin" id="sync-icon" style="display:none"></i> Sync Wazuh</button>
      <button class="btn btn-danger btn-sm" onclick="quickSimulate()">Simulate Attack</button>
    </div>

    <!-- Content -->
    <div id="content">

      <!-- ════ PAGE: OVERVIEW ════ -->
      <div class="page active" id="page-overview">
        <div class="page-header">
          <div>
            <div class="page-title">SOC Overview</div>
            <div class="page-sub">Real-time incident statistics from database</div>
          </div>
          <button class="btn btn-outline btn-sm" onclick="loadOverview()"><i class="fas fa-rotate"></i> Refresh</button>
        </div>

        <div class="stat-grid" id="stat-grid">
          <div class="stat-card"><div class="stat-label">Total Incidents</div><div class="stat-value" id="stat-total">—</div><div class="stat-sub">All time</div></div>
          <div class="stat-card"><div class="stat-label">Open</div><div class="stat-value" style="color:var(--red)" id="stat-open">—</div><div class="stat-sub">Needs attention</div></div>
          <div class="stat-card"><div class="stat-label">Critical</div><div class="stat-value" style="color:var(--red)" id="stat-critical">—</div><div class="stat-sub">Severity &ge; 10</div></div>
          <div class="stat-card"><div class="stat-label">Evidence Files</div><div class="stat-value" style="color:var(--blue)" id="stat-evidence">—</div><div class="stat-sub">DFIR artifacts</div></div>
          <div class="stat-card"><div class="stat-label">Response Actions</div><div class="stat-value" style="color:var(--green)" id="stat-actions">—</div><div class="stat-sub">Executed</div></div>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
          <div class="panel">
            <div class="panel-head">Recent Incidents <span style="color:var(--muted);font-size:10px;font-weight:400">Last 10</span></div>
            <table class="data-table" id="overview-table">
              <thead><tr><th>Incident ID</th><th>User</th><th>Severity</th><th>Status</th><th>Source</th></tr></thead>
              <tbody id="overview-tbody"><tr><td colspan="5" class="loading">Loading...</td></tr></tbody>
            </table>
          </div>
          <div class="panel">
            <div class="panel-head">Wazuh Integration Status</div>
            <div class="panel-body" id="wazuh-status-panel">
              <div class="loading">Checking Wazuh API...</div>
            </div>
          </div>
        </div>
      </div>

      <!-- ════ PAGE: ALERTS ════ -->
      <div class="page" id="page-alerts">
        <div class="page-header">
          <div><div class="page-title">Security Alerts</div><div class="page-sub">All detected incidents — filter, search, and investigate</div></div>
        </div>
        <div class="filter-bar">
          <input type="text" id="alert-search" placeholder="Search incident ID, user, IP..." style="width:220px" oninput="loadAlerts()">
          <select id="alert-status" onchange="loadAlerts()">
            <option value="">All Status</option>
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="CONTAINED">Contained</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
            <option value="FALSE_POSITIVE">False Positive</option>
          </select>
          <select id="alert-severity" onchange="loadAlerts()">
            <option value="">All Severity</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
          </select>
          <button class="btn btn-outline btn-sm" onclick="loadAlerts()"><i class="fas fa-rotate"></i></button>
        </div>
        <div class="panel">
          <table class="data-table" id="alerts-table">
            <thead><tr>
              <th>Incident ID</th><th>Timestamp</th><th>Target User</th>
              <th>Source IP</th><th>Agent</th><th>Severity</th>
              <th>MITRE</th><th>Status</th><th>Src</th><th>Actions</th>
            </tr></thead>
            <tbody id="alerts-tbody"><tr><td colspan="10" class="loading">Loading...</td></tr></tbody>
          </table>
          <div style="padding:8px 10px;" id="alerts-pagination"></div>
        </div>
      </div>

      <!-- ════ PAGE: INCIDENT DETAIL (sub-view) ════ -->
      <div class="page" id="page-incident-detail">
        <div class="page-header">
          <div>
            <div class="page-title" id="detail-title">Incident Detail</div>
            <div class="page-sub" id="detail-sub"></div>
          </div>
          <div style="display:flex;gap:8px;">
            <button class="btn btn-outline btn-sm" onclick="showPage('alerts')"><i class="fas fa-arrow-left"></i> Back</button>
            <a id="detail-pdf-btn" href="#" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-file-pdf"></i> Download PDF</a>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:2fr 1fr;gap:14px;">
          <!-- Left column -->
          <div style="display:flex;flex-direction:column;gap:14px;">
            <div class="panel">
              <div class="panel-head">Incident Details</div>
              <div class="panel-body" id="detail-fields"></div>
            </div>
            <div class="panel">
              <div class="panel-head">Event Timeline (Windows Event 4625)</div>
              <table class="data-table" id="detail-timeline">
                <thead><tr><th>#</th><th>Timestamp</th><th>User</th><th>Sub-Status</th><th>Source IP</th></tr></thead>
                <tbody id="detail-timeline-body"><tr><td colspan="5" class="loading">Loading...</td></tr></tbody>
              </table>
            </div>
            <div class="panel">
              <div class="panel-head">DFIR Evidence Artifacts <button class="btn btn-primary btn-sm" onclick="collectEvidence()" style="margin-left:8px">Collect Now</button></div>
              <table class="data-table" id="detail-evidence-table">
                <thead><tr><th>Type</th><th>File</th><th>SHA-256</th><th>Result</th><th>Collected</th><th>Action</th></tr></thead>
                <tbody id="detail-evidence-body"><tr><td colspan="6" class="empty">No evidence collected yet</td></tr></tbody>
              </table>
            </div>
          </div>
          <!-- Right column -->
          <div style="display:flex;flex-direction:column;gap:14px;">
            <div class="panel">
              <div class="panel-head">Status</div>
              <div class="panel-body">
                <select id="detail-status" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-bottom:8px;">
                  <option>OPEN</option><option>INVESTIGATING</option><option>CONTAINED</option>
                  <option>RESOLVED</option><option>CLOSED</option><option>FALSE_POSITIVE</option>
                </select>
                <input id="detail-actor" placeholder="Analyst name" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-bottom:8px;" value="Analyst">
                <button class="btn btn-primary btn-sm" style="width:100%" onclick="updateStatus()">Update Status</button>
              </div>
            </div>
            <div class="panel">
              <div class="panel-head">Investigation Notes</div>
              <div class="panel-body">
                <div id="notes-list" style="margin-bottom:10px;max-height:200px;overflow-y:auto;"></div>
                <textarea class="note-input" id="note-text" placeholder="Add investigation note..."></textarea>
                <input id="note-analyst" placeholder="Your name" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin:6px 0;margin-top:4px;" value="Analyst">
                <button class="btn btn-outline btn-sm" style="width:100%" onclick="addNote()">Add Note</button>
              </div>
            </div>
            <div class="panel">
              <div class="panel-head">Response Actions</div>
              <div class="panel-body">
                <select id="resp-action" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-bottom:6px;">
                  <option value="NOTIFY">Notify Analyst</option>
                  <option value="TAG_INCIDENT">Tag Incident</option>
                  <option value="BLOCK_IP">Block Source IP</option>
                  <option value="LOCK_ACCOUNT">Lock Account</option>
                  <option value="ISOLATE_HOST">Isolate Host</option>
                </select>
                <input id="resp-target" placeholder="Target (IP / hostname / account)" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-bottom:6px;">
                <label style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted);margin-bottom:8px;">
                  <input type="checkbox" id="resp-confirm"> Confirm disruptive action
                </label>
                <button class="btn btn-danger btn-sm" style="width:100%" onclick="executeResponse()">Execute</button>
                <div id="resp-results" style="margin-top:8px;"></div>
              </div>
              <!-- Response history for this incident -->
              <table class="data-table" style="margin-top:0">
                <thead><tr><th>ID</th><th>Incident</th><th>Action</th><th>Target</th><th>Status</th><th>Result</th><th>Executed</th></tr></thead>
                <tbody id="detail-response-tbody"><tr><td colspan="7" class="empty">No actions yet</td></tr></tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- ════ PAGE: INCIDENTS ════ -->
      <div class="page" id="page-incidents">
        <div class="page-header">
          <div><div class="page-title">Incident Management</div><div class="page-sub">Click any row to investigate</div></div>
        </div>
        <div class="filter-bar">
          <input type="text" id="inc-search" placeholder="Search..." style="width:200px" oninput="loadIncidentMgmt()">
          <select id="inc-status" onchange="loadIncidentMgmt()">
            <option value="">All</option><option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option><option value="RESOLVED">Resolved</option>
          </select>
        </div>
        <div class="panel">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Timestamp</th><th>Target</th><th>Agent</th><th>Severity</th><th>Rule</th><th>Status</th><th>Source</th></tr></thead>
            <tbody id="inc-mgmt-tbody"><tr><td colspan="8" class="loading">Loading...</td></tr></tbody>
          </table>
        </div>
      </div>

      <!-- ════ PAGE: EVIDENCE ════ -->
      <div class="page" id="page-evidence">
        <div class="page-header">
          <div><div class="page-title">DFIR Evidence</div><div class="page-sub">All collected forensic artifacts across incidents with SHA-256 integrity hashes</div></div>
          <button class="btn btn-outline btn-sm" onclick="loadAllEvidence()"><i class="fas fa-rotate"></i> Refresh</button>
        </div>
        <div class="panel">
          <div class="panel-head">All Forensic Evidence Artifacts</div>
          <table class="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Incident</th>
                <th>Type</th>
                <th>File</th>
                <th>SHA-256 Hash</th>
                <th>Result</th>
                <th>Acquired</th>
                <th>Integrity</th>
              </tr>
            </thead>
            <tbody id="all-evidence-tbody">
              <tr><td colspan="8" class="loading">Loading evidence artifacts...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- ════ PAGE: RESPONSE ════ -->
      <div class="page" id="page-response">
        <div class="page-header">
          <div><div class="page-title">Response Actions</div><div class="page-sub">Executed response actions and their results</div></div>
        </div>
        <div class="panel">
          <div class="panel-head">All Response Actions</div>
          <table class="data-table">
            <thead><tr><th>ID</th><th>Incident</th><th>Action</th><th>Target</th><th>Status</th><th>Result</th><th>Executed At</th></tr></thead>
            <tbody id="response-tbody"><tr><td colspan="7" class="loading">Loading...</td></tr></tbody>
          </table>
        </div>
      </div>

      <!-- ════ PAGE: REPORTS ════ -->
      <div class="page" id="page-reports">
        <div class="page-header">
          <div><div class="page-title">PDF Reports</div><div class="page-sub">Download auto-generated DFIR incident reports</div></div>
        </div>
        <div class="panel">
          <table class="data-table">
            <thead><tr><th>Incident ID</th><th>Timestamp</th><th>Severity</th><th>Target User</th><th>Status</th><th>Report</th></tr></thead>
            <tbody id="reports-tbody"><tr><td colspan="6" class="loading">Loading...</td></tr></tbody>
          </table>
        </div>
      </div>

      <!-- ════ PAGE: AUDIT ════ -->
      <div class="page" id="page-audit">
        <div class="page-header">
          <div><div class="page-title">Audit Logs</div><div class="page-sub">Immutable audit trail of all system operations</div></div>
          <button class="btn btn-outline btn-sm" onclick="loadAudit()"><i class="fas fa-rotate"></i> Refresh</button>
        </div>
        <div class="panel">
          <table class="data-table">
            <thead><tr><th>ID</th><th>Time</th><th>Event</th><th>Incident</th><th>Actor</th><th>Detail</th></tr></thead>
            <tbody id="audit-tbody"><tr><td colspan="6" class="loading">Loading...</td></tr></tbody>
          </table>
        </div>
      </div>

      <!-- ════ PAGE: HEALTH ════ -->
      <div class="page" id="page-health">
        <div class="page-header">
          <div><div class="page-title">System Health</div><div class="page-sub">Backend, database, and Wazuh integration status</div></div>
          <button class="btn btn-outline btn-sm" onclick="loadHealth()"><i class="fas fa-rotate"></i> Refresh</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
          <div class="panel">
            <div class="panel-head">Backend Health</div>
            <div class="panel-body" id="health-backend"><div class="loading">Loading...</div></div>
          </div>
          <div class="panel">
            <div class="panel-head">Wazuh API Detail</div>
            <div class="panel-body" id="health-wazuh"><div class="loading">Loading...</div></div>
          </div>
        </div>
      </div>

      <!-- ════ PAGE: SETTINGS ════ -->
      <div class="page" id="page-settings">
        <div class="page-header"><div><div class="page-title">Settings</div><div class="page-sub">Configuration and simulation controls</div></div></div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;">
          <div class="panel">
            <div class="panel-head">Simulate Brute-Force Attack</div>
            <div class="panel-body">
              <p style="color:var(--muted);font-size:11px;margin-bottom:12px;">
                Creates a simulated CRITICAL incident labelled [SIMULATED] in the database. Used for demo and testing only.
              </p>
              <div class="kv-block"><div class="kv-label">Target User</div>
                <input id="sim-user" value="Administrator" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-top:2px;"></div>
              <div class="kv-block" style="margin-top:8px;"><div class="kv-label">Source IP</div>
                <input id="sim-ip" value="192.168.31.105" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-top:2px;"></div>
              <div class="kv-block" style="margin-top:8px;"><div class="kv-label">Agent Name</div>
                <input id="sim-agent" value="DESKTOP-BJ2IO2A" style="width:100%;background:#FFFFFF;border:1px solid var(--border);color:var(--text);padding:6px;border-radius:4px;font-size:12px;margin-top:2px;"></div>
              <button class="btn btn-danger" style="margin-top:12px;width:100%" onclick="runSimulation()">Run Simulation</button>
              <div id="sim-result" style="margin-top:8px;font-size:11px;"></div>
            </div>
          </div>
          <div class="panel">
            <div class="panel-head">Project Information</div>
            <div class="panel-body">
              <div class="health-row"><span class="health-key">Project</span><span class="health-val">Automated SOC IR + DFIR</span></div>
              <div class="health-row"><span class="health-key">Author</span><span class="health-val">Karishma L</span></div>
              <div class="health-row"><span class="health-key">Institution</span><span class="health-val">KCG College of Technology</span></div>
              <div class="health-row"><span class="health-key">University</span><span class="health-val">Anna University</span></div>
              <div class="health-row"><span class="health-key">Degree</span><span class="health-val">B.E. CSE (Cyber Security)</span></div>
              <div class="health-row"><span class="health-key">Backend</span><span class="health-val">FastAPI + SQLite</span></div>
              <div class="health-row"><span class="health-key">SIEM</span><span class="health-val">Wazuh v4.14.7</span></div>
              <div class="health-row"><span class="health-key">PDF Engine</span><span class="health-val">ReportLab</span></div>
              <div class="health-row"><span class="health-key">Rule</span><span class="health-val">100051 (5 fails / 120s)</span></div>
            </div>
          </div>
        </div>
      </div>

    </div><!-- /content -->
  </div><!-- /main -->
</div><!-- /app -->

<script>
// ── State ──────────────────────────────────────────────────────────────────
let currentPage = 'overview';
let currentIncidentId = null;
let alertsOffset = 0;
const PAGE_SIZE = 25;

// ── Navigation ──────────────────────────────────────────────────────────────
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  const navEl = document.getElementById('nav-' + name);
  if (navEl) navEl.classList.add('active');
  currentPage = name;

  const titles = {
    overview: 'SOC Overview', alerts: 'Security Alerts',
    incidents: 'Incident Management', evidence: 'DFIR Evidence',
    response: 'Response Actions', reports: 'PDF Reports',
    audit: 'Audit Logs', health: 'System Health', settings: 'Settings',
    'incident-detail': 'Incident Detail',
  };
  document.getElementById('topbar-title').textContent = titles[name] || name;

  // Load data for the page
  if (name === 'overview') loadOverview();
  if (name === 'alerts') loadAlerts();
  if (name === 'incidents') loadIncidentMgmt();
  if (name === 'evidence') loadAllEvidence();
  if (name === 'reports') loadReports();
  if (name === 'audit') loadAudit();
  if (name === 'health') loadHealth();
  if (name === 'response') loadAllResponses();
}

// ── API helpers ─────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

function toast(msg, color='var(--text)') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.style.color = color;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 4500);
}

function severityBadge(sev, lvl) {
  const cls = (lvl >= 10) ? 'badge-red' : (lvl >= 7) ? 'badge-orange' : 'badge-muted';
  return `<span class="badge ${cls}">${sev || 'LVL ' + lvl}</span>`;
}

function statusBadge(s) {
  const map = {
    OPEN: 'badge-red', INVESTIGATING: 'badge-orange', CONTAINED: 'badge-blue',
    RESOLVED: 'badge-green', CLOSED: 'badge-muted', FALSE_POSITIVE: 'badge-muted'
  };
  return `<span class="badge ${map[s] || 'badge-muted'}">${s || 'OPEN'}</span>`;
}

function sourceBadge(src) {
  if (!src || src === 'SIMULATED') return `<span class="src-sim">[SIM]</span>`;
  if (src === 'WAZUH_SYNC' || src === 'WAZUH_WEBHOOK') return `<span class="src-real">[WAZUH]</span>`;
  return `<span class="src-sim">[${src}]</span>`;
}

function shortHash(h) {
  return h ? h.slice(0, 16) + '...' : '—';
}

function fmtTs(ts) {
  if (!ts) return '—';
  return ts.slice(0, 19).replace('T', ' ');
}

// ── Overview ────────────────────────────────────────────────────────────────
async function loadOverview() {
  // Stats
  try {
    const s = await api('/api/v1/stats');
    document.getElementById('stat-total').textContent = s.total_incidents ?? '—';
    document.getElementById('stat-open').textContent = s.open_incidents ?? '—';
    document.getElementById('stat-critical').textContent = s.critical_incidents ?? '—';
    document.getElementById('stat-evidence').textContent = s.evidence_records ?? '—';
    document.getElementById('stat-actions').textContent = s.response_actions ?? '—';
    if (s.open_incidents > 0) {
      const b = document.getElementById('open-badge');
      b.textContent = s.open_incidents;
      b.style.display = 'inline';
    }
  } catch(e) {}

  // Recent incidents
  try {
    const incs = await api('/api/v1/incidents?limit=10');
    const tb = document.getElementById('overview-tbody');
    if (!incs.length) { tb.innerHTML = '<tr><td colspan="5" class="empty">No incidents yet</td></tr>'; return; }
    tb.innerHTML = incs.map(i => `
      <tr style="cursor:pointer" onclick="openIncident('${i.incident_id}')">
        <td class="mono-cell">${i.incident_id}</td>
        <td>${i.target_user || '—'}</td>
        <td>${severityBadge(i.severity, i.severity_level)}</td>
        <td>${statusBadge(i.status)}</td>
        <td>${sourceBadge(i.data_source)}</td>
      </tr>`).join('');
  } catch(e) {
    document.getElementById('overview-tbody').innerHTML = `<tr><td colspan="5" style="color:var(--red);padding:12px;">${e.message}</td></tr>`;
  }

  // Wazuh status panel
  loadWazuhStatusPanel();
}

async function loadWazuhStatusPanel() {
  const panel = document.getElementById('wazuh-status-panel');
  try {
    const s = await api('/api/v1/wazuh/status');
    const dot = document.getElementById('wazuh-dot');
    const lbl = document.getElementById('wazuh-label');
    if (s.connected) {
      dot.className = 'dot ok';
      lbl.textContent = `Wazuh: ${s.status}`;
      lbl.style.color = '#39816C';
    } else {
      dot.className = 'dot err';
      lbl.textContent = `Wazuh: ${s.status}`;
      lbl.style.color = '#B64040';
    }

    panel.innerHTML = Object.entries({
      'Status': `<span style="color:${s.connected?'#39816C':'#B64040'};font-weight:600">${s.status}</span>`,
      'Manager IP': s.wazuh_ip,
      'API Port': s.wazuh_port,
      'API Version': s.api_version || '—',
      'Hostname': s.hostname || '—',
      'Message': s.message,
      'Checked At': fmtTs(s.checked_at),
    }).map(([k,v]) => `<div class="health-row"><span class="health-key">${k}</span><span class="health-val">${v}</span></div>`).join('');
  } catch(e) {
    panel.innerHTML = `<div style="color:var(--red);font-size:12px;">${e.message}</div>`;
  }
}

// ── Alerts ──────────────────────────────────────────────────────────────────
async function loadAlerts() {
  const search = document.getElementById('alert-search').value.trim();
  const status = document.getElementById('alert-status').value;
  const severity = document.getElementById('alert-severity').value;
  const tb = document.getElementById('alerts-tbody');
  tb.innerHTML = '<tr><td colspan="10" class="loading">Loading...</td></tr>';
  try {
    let url = `/api/v1/incidents?limit=${PAGE_SIZE}&offset=${alertsOffset}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${status}`;
    if (severity) url += `&severity=${severity}`;
    const incs = await api(url);
    if (!incs.length) { tb.innerHTML = '<tr><td colspan="10" class="empty">No incidents match the filter</td></tr>'; return; }
    tb.innerHTML = incs.map(i => `
      <tr style="cursor:pointer" onclick="openIncident('${i.incident_id}')">
        <td class="mono-cell" style="color:var(--blue);font-weight:600">${i.incident_id}</td>
        <td class="mono-cell">${fmtTs(i.timestamp)}</td>
        <td>${i.target_user || '—'}</td>
        <td class="mono-cell">${i.source_ip || '—'}</td>
        <td>${i.agent_name || '—'}</td>
        <td>${severityBadge(i.severity, i.severity_level)}</td>
        <td class="mono-cell" style="font-size:10px">${i.mitre_id || '—'}</td>
        <td>${statusBadge(i.status)}</td>
        <td>${sourceBadge(i.data_source)}</td>
        <td><button class="btn btn-outline btn-sm" onclick="event.stopPropagation();openIncident('${i.incident_id}')">Investigate</button></td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="10" style="color:var(--red);padding:12px;">${e.message}</td></tr>`;
  }
}

// ── Incident Detail ──────────────────────────────────────────────────────────
async function openIncident(id) {
  currentIncidentId = id;
  showPage('incident-detail');
  document.getElementById('detail-title').textContent = id;
  document.getElementById('detail-sub').textContent = 'Loading...';
  document.getElementById('detail-pdf-btn').href = `/api/v1/incidents/${id}/report`;

  try {
    const inc = await api(`/api/v1/incidents/${id}`);
    document.getElementById('detail-sub').textContent =
      `${fmtTs(inc.timestamp)} | ${inc.agent_name} | ${inc.mitre_id}`;

    // Status
    const statusEl = document.getElementById('detail-status');
    statusEl.value = inc.status || 'OPEN';

    // Fields
    const fields = [
      ['Incident ID', inc.incident_id],
      ['Timestamp', fmtTs(inc.timestamp)],
      ['Severity', `${inc.severity} (Level ${inc.severity_level})`],
      ['Rule ID', inc.rule_id],
      ['Rule Description', inc.rule_description],
      ['Agent ID', inc.agent_id],
      ['Agent Name', inc.agent_name],
      ['Target User', `<b style="color:#f85149">${inc.target_user || '—'}</b>`],
      ['Source IP', inc.source_ip],
      ['Workstation', inc.workstation],
      ['Logon Type', inc.logon_type],
      ['MITRE Tactic', inc.mitre_tactic],
      ['MITRE Technique', inc.mitre_technique],
      ['MITRE ID', inc.mitre_id],
      ['Data Source', sourceBadge(inc.data_source)],
      ['Evidence Hash', inc.evidence_hash ? `<span class="hash-cell">${inc.evidence_hash}</span>` : '—'],
    ];
    document.getElementById('detail-fields').innerHTML =
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:6px 16px;">' +
      fields.map(([k,v]) => `<div class="kv-block"><div class="kv-label">${k}</div><div class="kv-value">${v || '—'}</div></div>`).join('') +
      '</div>';

    // Timeline
    const events = inc.evidence_events || (inc._full ? inc._full.evidence_events : []) || [];
    const tlb = document.getElementById('detail-timeline-body');
    if (!events.length) {
      tlb.innerHTML = '<tr><td colspan="5" class="empty">No timeline events</td></tr>';
    } else {
      tlb.innerHTML = events.map((ev, i) => `
        <tr>
          <td class="mono-cell">${i+1}</td>
          <td class="mono-cell">${ev.timestamp || '—'}</td>
          <td>${ev.target_user || '—'}</td>
          <td class="mono-cell" style="font-size:10px">${ev.sub_status || '—'}</td>
          <td class="mono-cell">${ev.source_ip || '—'}</td>
        </tr>`).join('');
    }

    // Load evidence
    loadDetailEvidence(id);

    // Load notes
    loadNotes(id);

    // Load response results
    loadDetailResponse(id);

  } catch(e) {
    document.getElementById('detail-sub').textContent = 'Error: ' + e.message;
  }
}

async function loadDetailEvidence(id) {
  const tb = document.getElementById('detail-evidence-body');
  try {
    const ev = await api(`/api/v1/incidents/${id}/evidence`);
    if (!ev.length) { tb.innerHTML = '<tr><td colspan="6" class="empty">No evidence collected</td></tr>'; return; }
    tb.innerHTML = ev.map(e => `
      <tr class="${e.collection_result==='SUCCESS'?'ev-row-ok':e.collection_result==='UNAVAILABLE'?'ev-row-unavail':'ev-row-fail'}">
        <td><span class="badge badge-muted">${e.artifact_type}</span></td>
        <td class="mono-cell">${e.filename}</td>
        <td class="hash-cell">${shortHash(e.sha256_hash)}</td>
        <td><span class="badge ${e.collection_result==='SUCCESS'?'badge-green':e.collection_result==='UNAVAILABLE'?'badge-orange':'badge-red'}">${e.collection_result}</span></td>
        <td class="mono-cell">${fmtTs(e.collection_ts)}</td>
        <td><button class="btn btn-outline btn-sm" onclick="verifyEvidence(${e.id})">Verify</button></td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="6" style="color:var(--red)">${e.message}</td></tr>`;
  }
}

async function collectEvidence() {
  if (!currentIncidentId) return;
  toast('Collecting DFIR evidence — running OS commands...', '#e3b341');
  try {
    const res = await api(`/api/v1/incidents/${currentIncidentId}/evidence/collect`, { method: 'POST' });
    toast(`Evidence collected: ${res.artifacts_succeeded}/${res.artifacts_attempted} succeeded`, '#3fb950');
    loadDetailEvidence(currentIncidentId);
  } catch(e) {
    toast('Evidence collection error: ' + e.message, '#f85149');
  }
}

async function verifyEvidence(evidenceId) {
  try {
    const res = await api(`/api/v1/evidence/${evidenceId}/verify`, { method: 'POST' });
    toast(`Hash ${res.result}: ${res.computed_hash ? res.computed_hash.slice(0,16)+'...' : ''}`, res.verified ? '#3fb950' : '#f85149');
    loadDetailEvidence(currentIncidentId);
  } catch(e) {
    toast('Verify error: ' + e.message, '#f85149');
  }
}

// ── Notes ────────────────────────────────────────────────────────────────────
async function loadNotes(id) {
  try {
    const notes = await api(`/api/v1/incidents/${id}/notes`);
    const el = document.getElementById('notes-list');
    if (!notes.length) { el.innerHTML = '<div style="color:var(--muted);font-size:11px;">No notes yet.</div>'; return; }
    el.innerHTML = notes.map(n => `
      <div class="note-entry">
        <div class="note-meta">${n.analyst} &bull; ${fmtTs(n.created_at)}</div>
        <div class="note-text">${n.note}</div>
      </div>`).join('');
  } catch(e) {}
}

async function addNote() {
  const note = document.getElementById('note-text').value.trim();
  const analyst = document.getElementById('note-analyst').value.trim() || 'Analyst';
  if (!note) { toast('Note cannot be empty', '#f85149'); return; }
  try {
    await api(`/api/v1/incidents/${currentIncidentId}/notes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ analyst, note }),
    });
    document.getElementById('note-text').value = '';
    toast('Note added', '#3fb950');
    loadNotes(currentIncidentId);
  } catch(e) {
    toast('Error: ' + e.message, '#f85149');
  }
}

// ── Status Update ────────────────────────────────────────────────────────────
async function updateStatus() {
  const status = document.getElementById('detail-status').value;
  const actor = document.getElementById('detail-actor').value.trim() || 'Analyst';
  try {
    await api(`/api/v1/incidents/${currentIncidentId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, actor }),
    });
    toast(`Status updated to ${status}`, '#3fb950');
  } catch(e) {
    toast('Error: ' + e.message, '#f85149');
  }
}

// ── Response Actions ─────────────────────────────────────────────────────────
async function executeResponse() {
  const action = document.getElementById('resp-action').value;
  const target = document.getElementById('resp-target').value.trim();
  const confirmed = document.getElementById('resp-confirm').checked;
  if (!target) { toast('Target is required', '#f85149'); return; }
  const div = document.getElementById('resp-results');
  div.innerHTML = '<span style="color:var(--muted)">Executing...</span>';
  try {
    const res = await api(`/api/v1/incidents/${currentIncidentId}/response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_type: action, target, confirmed, authorized_by: 'Analyst' }),
    });
    div.innerHTML = `<div style="margin-top:6px;padding:8px;background:#DEF7EC;border:1px solid #BCF0DA;border-radius:4px;font-size:11px;color:#39816C;">
      <b>${res.status}</b> — ${res.result}</div>`;
    loadDetailResponse(currentIncidentId);
  } catch(e) {
    div.innerHTML = `<div style="margin-top:6px;padding:8px;background:#FDE8E8;border:1px solid #F8B4B4;border-radius:4px;color:#B64040;font-size:11px;">${e.message}</div>`;
  }
}

async function loadDetailResponse(id) {
  try {
    const actions = await api(`/api/v1/incidents/${id}/response`);
    const tb = document.getElementById('detail-response-tbody');
    if (!tb) return;
    if (!actions.length) {
      tb.innerHTML = '<tr><td colspan="7" class="empty">No response actions yet for this incident.</td></tr>';
      return;
    }
    tb.innerHTML = actions.map(a => `
      <tr>
        <td>${a.id}</td>
        <td class="mono-cell">${a.incident_id}</td>
        <td><span class="badge badge-blue">${a.action_type}</span></td>
        <td>${a.target || '—'}</td>
        <td><span class="badge ${a.status==='COMPLETED'?'badge-green':a.status==='MANUAL_REQUIRED'?'badge-orange':'badge-muted'}">${a.status}</span></td>
        <td style="font-size:11px;max-width:300px;white-space:normal">${a.result || '—'}</td>
        <td class="mono-cell">${fmtTs(a.executed_at)}</td>
      </tr>`).join('');
  } catch(e) {}
}

// ── Incident Management ──────────────────────────────────────────────────────
async function loadIncidentMgmt() {
  const search = document.getElementById('inc-search').value.trim();
  const status = document.getElementById('inc-status').value;
  const tb = document.getElementById('inc-mgmt-tbody');
  tb.innerHTML = '<tr><td colspan="8" class="loading">Loading...</td></tr>';
  try {
    let url = `/api/v1/incidents?limit=100`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${status}`;
    const incs = await api(url);
    if (!incs.length) { tb.innerHTML = '<tr><td colspan="8" class="empty">No incidents</td></tr>'; return; }
    tb.innerHTML = incs.map(i => `
      <tr style="cursor:pointer" onclick="openIncident('${i.incident_id}')">
        <td class="mono-cell" style="color:var(--blue);font-weight:600">${i.incident_id}</td>
        <td class="mono-cell">${fmtTs(i.timestamp)}</td>
        <td>${i.target_user||'—'}</td>
        <td>${i.agent_name||'—'}</td>
        <td>${severityBadge(i.severity, i.severity_level)}</td>
        <td class="mono-cell">${i.rule_id||'—'}</td>
        <td>${statusBadge(i.status)}</td>
        <td>${sourceBadge(i.data_source)}</td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="8" style="color:var(--red)">${e.message}</td></tr>`;
  }
}

// ── Reports ──────────────────────────────────────────────────────────────────
async function loadReports() {
  const tb = document.getElementById('reports-tbody');
  tb.innerHTML = '<tr><td colspan="6" class="loading">Loading...</td></tr>';
  try {
    const incs = await api('/api/v1/incidents?limit=100');
    if (!incs.length) { tb.innerHTML = '<tr><td colspan="6" class="empty">No incidents</td></tr>'; return; }
    tb.innerHTML = incs.map(i => `
      <tr>
        <td class="mono-cell">${i.incident_id}</td>
        <td class="mono-cell">${fmtTs(i.timestamp)}</td>
        <td>${severityBadge(i.severity, i.severity_level)}</td>
        <td>${i.target_user||'—'}</td>
        <td>${statusBadge(i.status)}</td>
        <td><a href="/api/v1/incidents/${i.incident_id}/report" target="_blank" class="btn btn-primary btn-sm"><i class="fas fa-file-pdf"></i> PDF</a></td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="6" style="color:var(--red)">${e.message}</td></tr>`;
  }
}

// ── Audit ────────────────────────────────────────────────────────────────────
async function loadAudit() {
  const tb = document.getElementById('audit-tbody');
  tb.innerHTML = '<tr><td colspan="6" class="loading">Loading...</td></tr>';
  try {
    const logs = await api('/api/v1/audit?limit=200');
    if (!logs.length) { tb.innerHTML = '<tr><td colspan="6" class="empty">No audit entries</td></tr>'; return; }
    tb.innerHTML = logs.map(l => `
      <tr>
        <td class="mono-cell">${l.id}</td>
        <td class="mono-cell">${fmtTs(l.created_at)}</td>
        <td><span class="badge badge-blue">${l.event_type}</span></td>
        <td class="mono-cell">${l.incident_id||'—'}</td>
        <td>${l.actor||'—'}</td>
        <td style="font-size:11px">${l.detail||'—'}</td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="6" style="color:var(--red)">${e.message}</td></tr>`;
  }
}

// ── Health ───────────────────────────────────────────────────────────────────
async function loadHealth() {
  try {
    const h = await api('/api/v1/health');
    document.getElementById('health-backend').innerHTML = Object.entries({
      'Status': `<span style="color:${h.status==='OK'?'#3fb950':'#f85149'}">${h.status}</span>`,
      'Version': h.version,
      'Database': `<span style="color:${h.database==='OK'?'#3fb950':'#f85149'}">${h.database}</span>`,
      'DB Path': h.db_path,
      'Reports Dir': h.reports_dir,
      'Wazuh Connected': `<span style="color:${h.wazuh_connected?'#3fb950':'#f85149'}">${h.wazuh_connected}</span>`,
      'Wazuh Status': h.wazuh_status,
      'Checked At': fmtTs(h.checked_at),
    }).map(([k,v])=>`<div class="health-row"><span class="health-key">${k}</span><span class="health-val">${v}</span></div>`).join('');
  } catch(e) {
    document.getElementById('health-backend').innerHTML = `<div style="color:var(--red)">${e.message}</div>`;
  }

  try {
    const w = await api('/api/v1/wazuh/status');
    document.getElementById('health-wazuh').innerHTML = Object.entries(w)
      .map(([k,v])=>`<div class="health-row"><span class="health-key">${k}</span><span class="health-val">${v}</span></div>`).join('');
  } catch(e) {
    document.getElementById('health-wazuh').innerHTML = `<div style="color:var(--red)">${e.message}</div>`;
  }
}

// ── All Evidence ─────────────────────────────────────────────────────────────
async function loadAllEvidence() {
  const tb = document.getElementById('all-evidence-tbody');
  if (!tb) return;
  tb.innerHTML = '<tr><td colspan="8" class="loading">Loading evidence artifacts...</td></tr>';
  try {
    const list = await api('/api/v1/evidence?limit=200');
    if (!list.length) {
      tb.innerHTML = '<tr><td colspan="8" class="empty">No evidence collected yet. Open an incident → click "Collect Now" to gather live DFIR artifacts.</td></tr>';
      return;
    }
    tb.innerHTML = list.map(e => `
      <tr class="${e.collection_result==='SUCCESS'?'ev-row-ok':e.collection_result==='UNAVAILABLE'?'ev-row-unavail':'ev-row-fail'}">
        <td>${e.id}</td>
        <td class="mono-cell" style="color:var(--blue);font-weight:600;cursor:pointer" onclick="openIncident('${e.incident_id}')">${e.incident_id}</td>
        <td><span class="badge badge-muted">${e.artifact_type}</span></td>
        <td class="mono-cell" title="${e.filepath||''}">${e.filename}</td>
        <td class="hash-cell" title="${e.sha256_hash||''}">${shortHash(e.sha256_hash)}</td>
        <td><span class="badge ${e.collection_result==='SUCCESS'?'badge-green':e.collection_result==='UNAVAILABLE'?'badge-orange':'badge-red'}">${e.collection_result}</span></td>
        <td class="mono-cell">${fmtTs(e.collection_ts)}</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="verifyGlobalEvidence(${e.id})">
            ${e.verify_result ? `<span class="badge ${e.verify_result==='MATCH'?'badge-green':'badge-red'}">${e.verify_result}</span>` : 'Verify'}
          </button>
        </td>
      </tr>
    `).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="8" style="color:var(--red);padding:12px;">${e.message}</td></tr>`;
  }
}

async function verifyGlobalEvidence(evidenceId) {
  try {
    const res = await api(`/api/v1/evidence/${evidenceId}/verify`, { method: 'POST' });
    toast(`Hash ${res.result}: ${res.computed_hash ? res.computed_hash.slice(0,16)+'...' : ''}`, res.verified ? '#39816C' : '#B64040');
    loadAllEvidence();
  } catch(e) {
    toast('Verify error: ' + e.message, '#B64040');
  }
}

// ── All Responses ────────────────────────────────────────────────────────────
async function loadAllResponses() {
  const tb = document.getElementById('response-tbody');
  tb.innerHTML = '<tr><td colspan="7" class="loading">Loading...</td></tr>';
  try {
    const actions = await api('/api/v1/response?limit=200');
    if (!actions.length) {
      tb.innerHTML = '<tr><td colspan="7" class="empty">No response actions yet. Open an incident → Response Actions panel → Execute an action.</td></tr>';
      return;
    }
    tb.innerHTML = actions.map(a => `
      <tr>
        <td>${a.id}</td>
        <td class="mono-cell" style="color:var(--blue);font-weight:600;cursor:pointer" onclick="openIncident('${a.incident_id}')">${a.incident_id||'—'}</td>
        <td><span class="badge badge-blue">${a.action_type||'—'}</span></td>
        <td>${a.target||'—'}</td>
        <td><span class="badge ${a.status==='COMPLETED'?'badge-green':a.status==='MANUAL_REQUIRED'?'badge-orange':'badge-muted'}">${a.status||'PENDING'}</span></td>
        <td style="font-size:11px;max-width:280px;white-space:normal">${a.result||'—'}</td>
        <td class="mono-cell">${fmtTs(a.executed_at||a.created_at)}</td>
      </tr>`).join('');
  } catch(e) {
    tb.innerHTML = `<tr><td colspan="7" style="color:var(--red);padding:12px;">${e.message}</td></tr>`;
  }
}

// ── Wazuh Sync ───────────────────────────────────────────────────────────────
async function syncWazuh() {
  const icon = document.getElementById('sync-icon');
  icon.style.display = 'inline-block';
  try {
    const res = await api('/api/v1/wazuh/sync');
    icon.style.display = 'none';
    if (res.synced) {
      toast(`Wazuh sync: ${res.new_incidents} new incidents from ${res.alerts_retrieved} alerts`, '#3fb950');
    } else {
      toast(`Wazuh sync failed: ${res.message}`, '#f85149');
    }
    loadOverview();
  } catch(e) {
    icon.style.display = 'none';
    toast('Sync error: ' + e.message, '#f85149');
  }
}

// ── Simulate ─────────────────────────────────────────────────────────────────
async function quickSimulate() {
  try {
    const res = await api('/api/v1/alerts/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_user: 'Administrator',
        failed_attempts: 5,
        source_ip: '192.168.31.105',
        workstation: 'DESKTOP-BJ2IO2A',
        agent_id: '001',
        agent_name: 'DESKTOP-BJ2IO2A'
      }),
    });

    // Red strobe flash
    const strobe = document.getElementById('strobe');
    strobe.classList.add('strobe-on');
    setTimeout(() => strobe.classList.remove('strobe-on'), 5000);

    // Toast notification
    toast(`[SIMULATED] Incident ${res.incident_id} created — ${res.target_user} @ ${res.agent_name}`, '#B64040');

    // Navigate to Security Alerts and reload so new incident appears at top
    showPage('alerts');
    alertsOffset = 0;
    await loadAlerts();

    // Also refresh overview stats
    loadOverview();

    // Highlight the newly created incident row after table loads
    setTimeout(() => {
      const rows = document.querySelectorAll('#alerts-tbody tr');
      if (rows[0]) {
        rows[0].style.background = 'rgba(182, 64, 64, 0.12)';
        rows[0].style.transition = 'background 2s';
        setTimeout(() => { rows[0].style.background = ''; }, 3000);
      }
    }, 600);

  } catch(e) {
    toast('Simulation failed: ' + e.message, '#B64040');
  }
}

async function runSimulation() {
  const user = document.getElementById('sim-user').value.trim() || 'Administrator';
  const ip = document.getElementById('sim-ip').value.trim() || '192.168.31.105';
  const agent = document.getElementById('sim-agent').value.trim() || 'DESKTOP-BJ2IO2A';
  const div = document.getElementById('sim-result');
  div.innerHTML = '<span style="color:var(--muted)">Running simulation...</span>';
  try {
    const res = await api('/api/v1/alerts/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_user: user, failed_attempts: 5, source_ip: ip, workstation: agent, agent_id: '001', agent_name: agent }),
    });
    div.innerHTML = `<div style="color:#3fb950">Created: ${res.incident_id}</div>
      <div style="color:var(--muted);font-size:10px">Severity: ${res.severity_level} | MITRE: ${res.mitre_id}</div>`;
  } catch(e) {
    div.innerHTML = `<div style="color:#f85149">${e.message}</div>`;
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
loadOverview();
loadWazuhStatusPanel();
// Poll every 10s for new incidents
setInterval(() => {
  if (currentPage === 'overview') loadOverview();
  if (currentPage === 'alerts') loadAlerts();
}, 10000);
</script>
</body>
</html>"""
