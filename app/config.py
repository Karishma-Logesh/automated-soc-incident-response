"""
app/config.py
Environment-based configuration.
Author: Karishma L — KCG College of Technology

All secrets are read from environment variables.
Set WAZUH_API_PASSWORD in a .env file or your shell before starting the server.
Never hardcode passwords here.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"
DATA_DIR = BASE_DIR / "data"
EVIDENCE_DIR = DATA_DIR / "evidence"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

# Wazuh SIEM Configuration (read from environment — never from source code)
WAZUH_MANAGER_IP = os.getenv("WAZUH_MANAGER_IP", "192.168.31.68")
WAZUH_API_PORT = os.getenv("WAZUH_API_PORT", "55000")
WAZUH_API_USER = os.getenv("WAZUH_API_USER", "wazuh")
WAZUH_MANAGER_VERSION = "4.14.7"

# Detection defaults
DEFAULT_AGENT_ID = "001"
DEFAULT_AGENT_NAME = "DESKTOP-BJ2IO2A"
BRUTE_FORCE_RULE_ID = "100051"
LOGON_FAILURE_RULE_ID = "60122"

# Thresholds
SEVERITY_THRESHOLD_CRITICAL = 10
AUTH_FAILURE_TIMEFRAME = 120  # seconds
AUTH_FAILURE_THRESHOLD = 5
