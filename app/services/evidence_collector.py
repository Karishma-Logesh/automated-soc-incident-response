"""
app/services/evidence_collector.py
DFIR Evidence Collection Service.
Author: Karishma L — KCG College of Technology

Collects forensic artifacts from the local Windows machine (where this server runs).
Artifacts collected:
  - Running processes (tasklist)
  - Active network connections (netstat)
  - Logged-in sessions (query session)
  - Recent Security event log entries (wevtutil, Event ID 4625)

Rules:
  - Only collects what is actually available with current privileges.
  - Records honest failures — never simulates success.
  - Saves artifacts to data/evidence/{incident_id}/ directory.
  - Calculates real SHA-256 hash from saved file.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.config import DATA_DIR

EVIDENCE_DIR = DATA_DIR / "evidence"
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)


def _sha256_of_file(filepath: Path) -> str:
    """Calculate real SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_cmd(cmd: list, timeout: int = 15) -> Dict[str, Any]:
    """
    Run a shell command and return output.
    Returns honest result — records permission errors and failures.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Command timed out", "returncode": -1}
    except PermissionError as e:
        return {"success": False, "stdout": "", "stderr": f"Permission denied: {e}", "returncode": -2}
    except FileNotFoundError as e:
        return {"success": False, "stdout": "", "stderr": f"Command not found: {e}", "returncode": -3}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -99}


def _save_artifact(incident_dir: Path, filename: str, content: str) -> Path:
    """Save artifact content to file and return its path."""
    incident_dir.mkdir(parents=True, exist_ok=True)
    filepath = incident_dir / filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def collect_processes(incident_id: str) -> Dict[str, Any]:
    """Collect running process list using tasklist (Windows) or ps (Linux)."""
    incident_dir = EVIDENCE_DIR / incident_id
    ts = datetime.now().isoformat()
    filename = f"processes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if platform.system() == "Windows":
        cmd = ["tasklist", "/fo", "csv", "/v"]
    else:
        cmd = ["ps", "aux"]

    result = _run_cmd(cmd)

    if result["success"] and result["stdout"].strip():
        header = f"# DFIR Evidence — Running Processes\n# Incident: {incident_id}\n# Collected: {ts}\n# Platform: {platform.system()}\n\n"
        content = header + result["stdout"]
        filepath = _save_artifact(incident_dir, filename, content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "PROCESSES",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "SUCCESS",
            "error": None,
            "collection_ts": ts,
        }
    else:
        # Record honest failure
        err = result["stderr"] or "No output returned"
        error_content = f"# DFIR Evidence — Processes FAILED\n# Incident: {incident_id}\n# Collected: {ts}\n# Error: {err}\n"
        filepath = _save_artifact(incident_dir, filename, error_content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "PROCESSES",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "FAILED",
            "error": err,
            "collection_ts": ts,
        }


def collect_network_connections(incident_id: str) -> Dict[str, Any]:
    """Collect active network connections using netstat."""
    incident_dir = EVIDENCE_DIR / incident_id
    ts = datetime.now().isoformat()
    filename = f"netstat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if platform.system() == "Windows":
        cmd = ["netstat", "-ano"]
    else:
        cmd = ["netstat", "-tulnp"]

    result = _run_cmd(cmd)

    if result["success"] and result["stdout"].strip():
        header = f"# DFIR Evidence — Active Network Connections\n# Incident: {incident_id}\n# Collected: {ts}\n# Platform: {platform.system()}\n\n"
        content = header + result["stdout"]
        filepath = _save_artifact(incident_dir, filename, content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "NETWORK_CONNECTIONS",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "SUCCESS",
            "error": None,
            "collection_ts": ts,
        }
    else:
        err = result["stderr"] or "No output"
        error_content = f"# DFIR Evidence — Network FAILED\n# Incident: {incident_id}\n# Error: {err}\n"
        filepath = _save_artifact(incident_dir, filename, error_content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "NETWORK_CONNECTIONS",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "FAILED",
            "error": err,
            "collection_ts": ts,
        }


def collect_sessions(incident_id: str) -> Dict[str, Any]:
    """Collect logged-in user sessions."""
    incident_dir = EVIDENCE_DIR / incident_id
    ts = datetime.now().isoformat()
    filename = f"sessions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if platform.system() == "Windows":
        cmd = ["query", "session"]
    else:
        cmd = ["who"]

    result = _run_cmd(cmd)

    content_lines = [
        f"# DFIR Evidence — Active Sessions",
        f"# Incident: {incident_id}",
        f"# Collected: {ts}",
        f"# Result: {'SUCCESS' if result['success'] else 'FAILED'}",
        "",
        result["stdout"] if result["success"] else f"ERROR: {result['stderr']}",
    ]
    content = "\n".join(content_lines)
    filepath = _save_artifact(incident_dir, filename, content)
    sha256 = _sha256_of_file(filepath)

    return {
        "artifact_type": "SESSIONS",
        "filename": filename,
        "filepath": str(filepath),
        "sha256_hash": sha256,
        "result": "SUCCESS" if result["success"] else "FAILED",
        "error": None if result["success"] else result["stderr"],
        "collection_ts": ts,
    }


def collect_security_events(incident_id: str, event_id: str = "4625",
                              count: int = 20) -> Dict[str, Any]:
    """
    Collect recent Windows Security event log entries (Event ID 4625 by default).
    Only works on Windows with appropriate privileges.
    """
    incident_dir = EVIDENCE_DIR / incident_id
    ts = datetime.now().isoformat()
    filename = f"security_events_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    if platform.system() != "Windows":
        content = f"# DFIR Evidence — Security Events\n# Incident: {incident_id}\n# Status: UNAVAILABLE\n# Reason: Windows Event Log requires Windows OS. This server is running on {platform.system()}.\n# Collection Timestamp: {ts}\n"
        filepath = _save_artifact(incident_dir, filename, content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "SECURITY_EVENTS",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "UNAVAILABLE",
            "error": f"Windows Event Log not available on {platform.system()}",
            "collection_ts": ts,
        }

    # Windows: use wevtutil
    cmd = [
        "wevtutil", "qe", "Security",
        f"/q:*[System[EventID={event_id}]]",
        f"/c:{count}",
        "/f:text",
        "/rd:true",
    ]
    result = _run_cmd(cmd, timeout=20)

    if result["success"] and result["stdout"].strip():
        header = f"# DFIR Evidence — Windows Security Events (Event ID {event_id})\n# Incident: {incident_id}\n# Collected: {ts}\n# Count requested: {count}\n\n"
        content = header + result["stdout"]
        filepath = _save_artifact(incident_dir, filename, content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "SECURITY_EVENTS",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "SUCCESS",
            "error": None,
            "collection_ts": ts,
        }
    else:
        err = result["stderr"] or "wevtutil returned no output (may need admin privileges)"
        error_content = f"# DFIR Evidence — Security Events FAILED\n# Incident: {incident_id}\n# Collected: {ts}\n# Event ID: {event_id}\n# Error: {err}\n# Note: 'wevtutil qe Security' requires administrator privileges on Windows.\n"
        filepath = _save_artifact(incident_dir, filename, error_content)
        sha256 = _sha256_of_file(filepath)
        return {
            "artifact_type": "SECURITY_EVENTS",
            "filename": filename,
            "filepath": str(filepath),
            "sha256_hash": sha256,
            "result": "FAILED",
            "error": err,
            "collection_ts": ts,
        }


def collect_all(incident_id: str) -> list:
    """
    Run all collectors for an incident.
    Returns list of artifact results — honest successes and failures.
    """
    collectors = [
        collect_processes,
        collect_network_connections,
        collect_sessions,
        collect_security_events,
    ]
    results = []
    for fn in collectors:
        try:
            results.append(fn(incident_id))
        except Exception as e:
            results.append({
                "artifact_type": fn.__name__.upper(),
                "filename": "error.txt",
                "filepath": "",
                "sha256_hash": None,
                "result": "ERROR",
                "error": str(e),
                "collection_ts": datetime.now().isoformat(),
            })
    return results


def verify_evidence_hash(filepath: str, stored_hash: str) -> Dict[str, Any]:
    """
    Recalculate SHA-256 of a saved evidence file and compare with stored hash.
    Returns honest verification result.
    """
    p = Path(filepath)
    if not p.exists():
        return {
            "verified": False,
            "result": "FILE_MISSING",
            "message": f"Evidence file not found: {filepath}",
            "stored_hash": stored_hash,
            "computed_hash": None,
        }
    try:
        computed = _sha256_of_file(p)
        match = computed == stored_hash
        return {
            "verified": match,
            "result": "MATCH" if match else "HASH_MISMATCH",
            "message": "Evidence integrity verified" if match else "WARNING: Hash mismatch — file may have been modified",
            "stored_hash": stored_hash,
            "computed_hash": computed,
        }
    except Exception as e:
        return {
            "verified": False,
            "result": "ERROR",
            "message": str(e),
            "stored_hash": stored_hash,
            "computed_hash": None,
        }
