# 🛡️ Automated SOC Incident Response & DFIR Platform
## 📌 Master Live Demo Run-Book & Presentation Guide

> **All files, scripts, models, and UI changes are permanently saved in:**  
> `C:\Users\Malar\.gemini\antigravity\scratch\soc_incident_response`

---

## ⚡ Quick 1-Click Launch (No Typing Needed!)

Whenever you restart your PC or start your presentation:

1. **Step 1:** Go to `C:\Users\Malar\.gemini\antigravity\scratch\soc_incident_response`
2. **Step 2:** Double-click **`run_dashboard.bat`**  
   *(This launches the FastAPI backend and SOC Platform on port 8000)*
3. **Step 3:** Open browser to **`http://localhost:8000`**
4. **Step 4:** Double-click **`run_attack_simulation.bat`**  
   *(This runs the automated 5 failed logon attempts in PowerShell)*
5. **Step 5:** Watch the live red strobe, siren, popup, and click **`Stop Siren`**!

---

## 🖥️ Live Demonstration Steps (For Judges / Faculty)

### 1. Baseline State (Before Attack)
- Dashboard URL: `http://localhost:8000`
- System Status: **DEFCON 5 • NORMAL** (Green indicator)
- SIEM: Connected to Wazuh (192.168.31.68)
- Target Endpoint: Windows 10 (Agent 001 - DESKTOP-BJ2IO2A)
- Explanation: *"The system is continuously ingesting Windows Security Event logs and monitoring for anomalies."*

### 2. Attack Execution
- Run `run_attack_simulation.bat` OR on Kali Linux run `sudo tail -f /var/ossec/logs/alerts/alerts.log | grep 100051`.
- Explanation: *"We are generating 5 rapid failed SMB authentication attempts (Event ID 4625) within a 120-second window."*

### 3. Real-Time Threat Reaction
- **Siren Sounds** automatically.
- **Red Emergency Strobe** flashes on the screen.
- Status escalates to **DEFCON 1 (CRITICAL THREAT)**.
- Telemetry line graph spikes past the 5-attempt threshold.
- A glowing red row with **`🔥 NEW ATTACK`** badge appears at the top of the table.
- A tactical floating **Attack Alert Pop-up** slides into the bottom-right corner.
- Action: Click **`[🛑 Stop Siren]`** (available on the top navbar, on the new attack row, or in the bottom-right pop-up).

### 4. DFIR Forensic Triage & PDF Evidence
- Click **`[👁️ Inspect]`** on the new row:
  - Displays reconstructed Event 4625 forensic stream with millisecond timestamps and `0xC000006A` error codes.
  - Displays AI Security Copilot automated threat attribution.
  - Displays cryptographic chain-of-custody digital hash (`SHA256`).
- Click **`[📄 PDF]`**:
  - Automatically downloads and opens the official DFIR Incident Report PDF.
  - Saved permanently on disk at:  
    `C:\Users\Malar\.gemini\antigravity\scratch\soc_incident_response\reports\`

---

## 📁 Key File Locations

| File / Folder | Path | Purpose |
|---|---|---|
| **Backend & Dashboard** | `app\main.py`, `app\api\routes.py` | FastAPI server + Interactive SOC Dashboard HTML/JS |
| **Start Server Script** | `run_dashboard.bat` | Starts Uvicorn server on port 8000 |
| **Attack Simulation Script** | `run_attack_simulation.bat` | 1-click batch script for attack execution |
| **PowerShell Simulator** | `scripts\simulate_bruteforce.ps1` | Generates 5 failed SMB logons (Event 4625) |
| **Generated DFIR Reports** | `reports\*.pdf` | Permanent storage for all incident PDF reports |
| **Database of Incidents** | `data\incidents.json` | Persistent incident feed database |
| **Custom Wazuh Rule** | `..\soc_wazuh\custom_rules\local_rules.xml` | Rule ID 100051 (Level 10 correlation) |
