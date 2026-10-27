"""
app/db.py
SQLite database layer for the SOC Incident Response platform.
Author: Karishma L — KCG College of Technology

Tables:
  incidents        — persisted incident records (migrated from incidents.json)
  investigation_notes — analyst notes per incident
  evidence_records — DFIR artifact metadata + SHA-256 hashes
  response_actions — executed response actions per incident
  audit_log        — immutable audit trail of all operations
"""

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.config import DATA_DIR

DB_PATH = DATA_DIR / "soc.db"
_lock = threading.Lock()


def get_conn() -> sqlite3.Connection:
    """Return a thread-safe SQLite connection with row_factory."""
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist, then migrate JSON incidents."""
    with _lock:
        conn = get_conn()
        cur = conn.cursor()

        # ── incidents ──────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS incidents (
                incident_id     TEXT PRIMARY KEY,
                timestamp       TEXT NOT NULL,
                severity        TEXT NOT NULL DEFAULT 'CRITICAL',
                severity_level  INTEGER NOT NULL DEFAULT 10,
                rule_id         TEXT,
                rule_description TEXT,
                agent_id        TEXT,
                agent_name      TEXT,
                target_user     TEXT,
                source_ip       TEXT,
                workstation     TEXT,
                logon_type      TEXT,
                mitre_tactic    TEXT,
                mitre_technique TEXT,
                mitre_id        TEXT,
                evidence_hash   TEXT,
                report_filename TEXT,
                report_download_url TEXT,
                status          TEXT NOT NULL DEFAULT 'OPEN',
                data_source     TEXT NOT NULL DEFAULT 'SIMULATED',
                raw_json        TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── investigation_notes ────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS investigation_notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id TEXT NOT NULL REFERENCES incidents(incident_id),
                analyst     TEXT NOT NULL DEFAULT 'Analyst',
                note        TEXT NOT NULL,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── evidence_records ───────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS evidence_records (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id     TEXT NOT NULL REFERENCES incidents(incident_id),
                artifact_type   TEXT NOT NULL,
                filename        TEXT NOT NULL,
                filepath        TEXT NOT NULL,
                sha256_hash     TEXT,
                collection_ts   TEXT NOT NULL,
                collection_result TEXT NOT NULL DEFAULT 'PENDING',
                error_message   TEXT,
                verified_at     TEXT,
                verify_result   TEXT
            )
        """)

        # ── response_actions ───────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS response_actions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                incident_id     TEXT NOT NULL REFERENCES incidents(incident_id),
                action_type     TEXT NOT NULL,
                target          TEXT,
                authorized_by   TEXT NOT NULL DEFAULT 'Analyst',
                status          TEXT NOT NULL DEFAULT 'PENDING',
                result          TEXT,
                executed_at     TEXT,
                created_at      TEXT DEFAULT (datetime('now'))
            )
        """)

        # ── audit_log ──────────────────────────────────────────────────────
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type  TEXT NOT NULL,
                incident_id TEXT,
                actor       TEXT NOT NULL DEFAULT 'system',
                detail      TEXT,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)

        conn.commit()

        # ── Migrate existing incidents.json → SQLite ───────────────────────
        json_path = DATA_DIR / "incidents.json"
        if json_path.exists():
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    old_incidents = json.load(f)

                migrated = 0
                for inc in old_incidents:
                    iid = inc.get("incident_id")
                    if not iid:
                        continue
                    exists = cur.execute(
                        "SELECT 1 FROM incidents WHERE incident_id=?", (iid,)
                    ).fetchone()
                    if exists:
                        continue
                    cur.execute("""
                        INSERT OR IGNORE INTO incidents
                        (incident_id, timestamp, severity, severity_level, rule_id,
                         rule_description, agent_id, agent_name, target_user, source_ip,
                         workstation, logon_type, mitre_tactic, mitre_technique, mitre_id,
                         evidence_hash, report_filename, report_download_url, status,
                         data_source, raw_json)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        iid,
                        inc.get("timestamp", datetime.now().isoformat()),
                        inc.get("severity", "CRITICAL"),
                        inc.get("severity_level", 10),
                        inc.get("rule_id"),
                        inc.get("rule_description"),
                        inc.get("agent_id"),
                        inc.get("agent_name"),
                        inc.get("target_user"),
                        inc.get("source_ip"),
                        inc.get("workstation"),
                        inc.get("logon_type"),
                        inc.get("mitre_tactic"),
                        inc.get("mitre_technique"),
                        inc.get("mitre_id"),
                        inc.get("evidence_hash"),
                        inc.get("report_filename"),
                        inc.get("report_download_url"),
                        "OPEN",
                        "SIMULATED",
                        json.dumps(inc),
                    ))
                    migrated += 1

                conn.commit()
                if migrated:
                    audit_add(conn, "DB_MIGRATION", None, "system",
                               f"Migrated {migrated} incidents from incidents.json")
            except Exception as e:
                print(f"[DB] Migration warning: {e}")

        conn.close()


# ── Helpers ────────────────────────────────────────────────────────────────

def audit_add(conn, event_type: str, incident_id: Optional[str],
               actor: str, detail: str):
    """Insert an audit log entry. conn may be external or a new connection."""
    conn.execute(
        "INSERT INTO audit_log (event_type, incident_id, actor, detail) VALUES (?,?,?,?)",
        (event_type, incident_id, actor, detail)
    )


def save_incident(inc: Dict[str, Any], data_source: str = "SIMULATED"):
    """Insert or ignore a new incident record."""
    with _lock:
        conn = get_conn()
        iid = inc.get("incident_id")
        conn.execute("""
            INSERT OR IGNORE INTO incidents
            (incident_id, timestamp, severity, severity_level, rule_id,
             rule_description, agent_id, agent_name, target_user, source_ip,
             workstation, logon_type, mitre_tactic, mitre_technique, mitre_id,
             evidence_hash, report_filename, report_download_url, status,
             data_source, raw_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            iid,
            inc.get("timestamp", datetime.now().isoformat()),
            inc.get("severity", "CRITICAL"),
            inc.get("severity_level", 10),
            inc.get("rule_id"),
            inc.get("rule_description"),
            inc.get("agent_id"),
            inc.get("agent_name"),
            inc.get("target_user"),
            inc.get("source_ip"),
            inc.get("workstation"),
            inc.get("logon_type"),
            inc.get("mitre_tactic"),
            inc.get("mitre_technique"),
            inc.get("mitre_id"),
            inc.get("evidence_hash"),
            inc.get("report_filename"),
            inc.get("report_download_url"),
            "OPEN",
            data_source,
            json.dumps(inc),
        ))
        audit_add(conn, "INCIDENT_CREATED", iid, "system",
                  f"source={data_source} severity={inc.get('severity_level')}")
        conn.commit()
        conn.close()


def list_incidents(limit: int = 200, offset: int = 0,
                   status: Optional[str] = None,
                   severity: Optional[str] = None,
                   search: Optional[str] = None) -> List[Dict]:
    conn = get_conn()
    clauses = []
    params: List[Any] = []
    if status:
        clauses.append("status=?"); params.append(status)
    if severity:
        clauses.append("severity=?"); params.append(severity)
    if search:
        clauses.append("(target_user LIKE ? OR source_ip LIKE ? OR incident_id LIKE ? OR agent_name LIKE ?)")
        params += [f"%{search}%"] * 4
    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = conn.execute(
        f"SELECT * FROM incidents {where} ORDER BY timestamp DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_incident(incident_id: str) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM incidents WHERE incident_id=?", (incident_id,)
    ).fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d.get("raw_json"):
            try:
                d["_full"] = json.loads(d["raw_json"])
            except Exception:
                pass
        return d
    return None


def update_incident_status(incident_id: str, new_status: str, actor: str = "analyst") -> bool:
    allowed = {"OPEN", "INVESTIGATING", "CONTAINED", "RESOLVED", "CLOSED", "FALSE_POSITIVE"}
    if new_status.upper() not in allowed:
        return False
    with _lock:
        conn = get_conn()
        conn.execute(
            "UPDATE incidents SET status=? WHERE incident_id=?",
            (new_status.upper(), incident_id)
        )
        audit_add(conn, "STATUS_CHANGE", incident_id, actor,
                  f"new_status={new_status.upper()}")
        conn.commit()
        conn.close()
    return True


def add_note(incident_id: str, analyst: str, note: str) -> int:
    with _lock:
        conn = get_conn()
        cur = conn.execute(
            "INSERT INTO investigation_notes (incident_id, analyst, note) VALUES (?,?,?)",
            (incident_id, analyst, note)
        )
        note_id = cur.lastrowid
        audit_add(conn, "NOTE_ADDED", incident_id, analyst, f"note_id={note_id}")
        conn.commit()
        conn.close()
    return note_id


def get_notes(incident_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM investigation_notes WHERE incident_id=? ORDER BY created_at",
        (incident_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_evidence(incident_id: str, artifact_type: str, filename: str,
                   filepath: str, sha256: Optional[str],
                   result: str, error: Optional[str] = None) -> int:
    with _lock:
        conn = get_conn()
        cur = conn.execute("""
            INSERT INTO evidence_records
            (incident_id, artifact_type, filename, filepath, sha256_hash,
             collection_ts, collection_result, error_message)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            incident_id, artifact_type, filename, filepath, sha256,
            datetime.now().isoformat(), result, error
        ))
        eid = cur.lastrowid
        audit_add(conn, "EVIDENCE_COLLECTED", incident_id, "system",
                  f"type={artifact_type} result={result} file={filename}")
        conn.commit()
        conn.close()
    return eid


def get_evidence(incident_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM evidence_records WHERE incident_id=? ORDER BY collection_ts DESC",
        (incident_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_all_evidence(limit: int = 100) -> List[Dict]:
    """Retrieve all evidence records across incidents."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM evidence_records ORDER BY collection_ts DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_evidence_verify(evidence_id: int, verify_result: str):
    with _lock:
        conn = get_conn()
        conn.execute(
            "UPDATE evidence_records SET verified_at=datetime('now'), verify_result=? WHERE id=?",
            (verify_result, evidence_id)
        )
        conn.commit()
        conn.close()


def save_response_action(incident_id: str, action_type: str, target: str,
                          authorized_by: str) -> int:
    with _lock:
        conn = get_conn()
        cur = conn.execute("""
            INSERT INTO response_actions
            (incident_id, action_type, target, authorized_by, status)
            VALUES (?,?,?,?,'PENDING')
        """, (incident_id, action_type, target, authorized_by))
        aid = cur.lastrowid
        audit_add(conn, "RESPONSE_ACTION_CREATED", incident_id, authorized_by,
                  f"action={action_type} target={target}")
        conn.commit()
        conn.close()
    return aid


def update_response_action(action_id: int, status: str, result: str):
    with _lock:
        conn = get_conn()
        conn.execute("""
            UPDATE response_actions
            SET status=?, result=?, executed_at=datetime('now')
            WHERE id=?
        """, (status, result, action_id))
        conn.commit()
        conn.close()


def get_response_actions(incident_id: str) -> List[Dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM response_actions WHERE incident_id=? ORDER BY created_at DESC",
        (incident_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_all_response_actions(limit: int = 100) -> List[Dict]:
    """Retrieve all response actions across all incidents."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM response_actions ORDER BY created_at DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_audit_log(limit: int = 100, incident_id: Optional[str] = None) -> List[Dict]:
    conn = get_conn()
    if incident_id:
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE incident_id=? ORDER BY created_at DESC LIMIT ?",
            (incident_id, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM audit_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> Dict:
    conn = get_conn()
    total = conn.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
    open_ = conn.execute("SELECT COUNT(*) FROM incidents WHERE status='OPEN'").fetchone()[0]
    critical = conn.execute(
        "SELECT COUNT(*) FROM incidents WHERE severity_level>=10"
    ).fetchone()[0]
    evidence_count = conn.execute("SELECT COUNT(*) FROM evidence_records").fetchone()[0]
    actions_count = conn.execute("SELECT COUNT(*) FROM response_actions").fetchone()[0]
    conn.close()
    return {
        "total_incidents": total,
        "open_incidents": open_,
        "critical_incidents": critical,
        "evidence_records": evidence_count,
        "response_actions": actions_count,
    }
