# Automated SOC Incident Response with DFIR Capabilities

An end-to-end automated SIEM & SOAR incident response pipeline that detects credential brute-force attacks via Wazuh custom correlation rules, triages and extracts digital forensic evidence via FastAPI, and generates publication-grade PDF incident response reports using ReportLab.

---

## 1. System Architecture

```
┌───────────────────────────────────────┐
│     Windows 10 Target Endpoint        │
│   (DESKTOP-BJ2IO2A / Agent ID 001)    │
│   Auditpol Enabled (Event ID 4625)    │
└──────────────────┬────────────────────┘
                   │ Wazuh Agent Protocol (TLS)
                   ▼
┌───────────────────────────────────────┐
│       Kali Linux Wazuh Manager        │
│         (192.168.31.68, v4.14)        │
│   Custom Rule 100051 (Level 10)       │
│   5 Failed Logins in 120s by User     │
└──────────────────┬────────────────────┘
                   │ Wazuh <integration> / HTTP Webhook
                   ▼
┌────────────────────────────────────────────────────────┐
│            FastAPI SOAR & DFIR Pipeline                │
│                                                        │
│  - Ingestion: POST /api/v1/alerts/webhook              │
│  - DFIR Engine: MITRE ATT&CK T1110.001 Mapping         │
│  - Timeline Reconstructor: Windows Event 4625 Analysis │
│  - ReportLab Engine: Automated PDF Incident Report     │
│  - Analyst UI: Interactive Live SOC Web Dashboard      │
└────────────────────────────────────────────────────────┘
```

---

## 2. Directory Structure

```
soc_incident_response/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py             # Webhook, simulation, and PDF download endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py            # Pydantic data schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── dfir_engine.py        # MITRE ATT&CK & forensic evidence parsing
│   │   └── report_generator.py   # ReportLab professional PDF generation
│   ├── config.py                 # System constants and paths
│   └── main.py                   # FastAPI server entry point
├── reports/                      # Auto-generated PDF incident reports
├── data/                         # Incident persistence store (incidents.json)
├── scripts/
│   ├── simulate_bruteforce.ps1   # PowerShell simulation script for Windows 10
│   └── custom-fastapi.py         # Kali Wazuh integration hook script
├── requirements.txt              # Python dependencies
└── README.md                     # Documentation
```

---

## 3. Quickstart & Installation

### Step 1: Install Dependencies
Open PowerShell or Command Prompt in the project folder and run:
```powershell
py -m pip install -r requirements.txt
```

### Step 2: Start the FastAPI Server
```powershell
py app/main.py
```
Or via Uvicorn:
```powershell
py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Once started:
- **SOC Web Dashboard**: Open `http://localhost:8000` in your browser.
- **Interactive Swagger API Docs**: Open `http://localhost:8000/docs`.

---

## 4. Testing & Incident Workflow

### Option A: One-Click Instant Simulation (UI)
1. Open `http://localhost:8000`.
2. Click the **"Simulate Attack (Rule 100051)"** button.
3. The incident will appear in the live feed immediately.
4. Click **"Download PDF"** to inspect the generated forensic report.

### Option B: Live Attack from Windows 10 Endpoint
1. On the Windows 10 endpoint (`DESKTOP-BJ2IO2A`), open PowerShell as Administrator and run:
   ```powershell
   .\scripts\simulate_bruteforce.ps1 -TargetUser "Administrator" -Attempts 5
   ```
2. On Kali Linux, confirm that Wazuh catches the attack:
   ```bash
   sudo tail -f /var/ossec/logs/alerts/alerts.log | grep -A 8 "100051"
   ```

---

## 5. Connecting Kali Wazuh Manager to FastAPI

To have Kali Linux automatically push alerts to FastAPI whenever Rule `100051` fires:

1. Copy `scripts/custom-fastapi.py` to Kali:
   ```bash
   sudo cp scripts/custom-fastapi.py /var/ossec/integrations/custom-fastapi
   sudo chown root:wazuh /var/ossec/integrations/custom-fastapi
   sudo chmod 750 /var/ossec/integrations/custom-fastapi
   ```

2. Add the integration to `/var/ossec/etc/ossec.conf` (inside `<ossec_config>`):
   ```xml
   <integration>
     <name>custom-fastapi</name>
     <rule_id>100051</rule_id>
     <hook_url>http://YOUR_FASTAPI_IP:8000/api/v1/alerts/webhook</hook_url>
     <alert_format>json</alert_format>
   </integration>
   ```

3. Restart Wazuh:
   ```bash
   sudo systemctl restart wazuh-manager
   ```

---

## 6. Generated DFIR Report Sections
The generated PDF report includes:
1. **Header Banner**: Incident ID, Timestamp, and CRITICAL Severity Badge.
2. **Executive Overview**: Wazuh Detection metadata, Manager IP (`192.168.31.68`), Rule `100051`.
3. **Targeted Asset Context**: Endpoint Hostname (`DESKTOP-BJ2IO2A`), Agent ID `001`, Target User, Logon Type.
4. **MITRE ATT&CK Classification**: Technique `T1110.001` (Brute Force: Password Guessing), Tactic `TA0006`.
5. **Forensic Evidence & Timeline**: Table detailing all 5 failed logon events with timestamps, sub-status codes, and IP addresses.
6. **DFIR Containment Action Plan**: Step-by-step containment checklist (Host isolation, account lockout, credential reset, log audit).
7. **Chain of Custody & Analyst Sign-off**: Evidence SHA-256 hash and formal review status.
