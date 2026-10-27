#!/usr/bin/env python3
"""
Wazuh Custom Integration Script: Forward Alerts to FastAPI SOAR Backend.

Deployment on Kali Linux (192.168.31.68):
1. Copy this script to: /var/ossec/integrations/custom-fastapi
2. Set ownership and permissions:
   sudo chown root:wazuh /var/ossec/integrations/custom-fastapi
   sudo chmod 750 /var/ossec/integrations/custom-fastapi

3. Add the following block into /var/ossec/etc/ossec.conf inside <ossec_config>:

   <integration>
     <name>custom-fastapi</name>
     <rule_id>100051</rule_id>
     <hook_url>http://192.168.31.50:8000/api/v1/alerts/webhook</hook_url>
     <alert_format>json</alert_format>
   </integration>

   *(Replace 192.168.31.50 with the IP of your machine running the FastAPI server).*

4. Restart Wazuh Manager:
   sudo systemctl restart wazuh-manager
"""

import sys
import json
import urllib.request
import urllib.error

def main():
    if len(sys.argv) < 2:
        print("Usage: custom-fastapi <alert_file_path> [user] [hook_url]", file=sys.stderr)
        sys.exit(1)

    alert_file_path = sys.argv[1]
    hook_url = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else "http://127.0.0.1:8000/api/v1/alerts/webhook"

    try:
        with open(alert_file_path, "r", encoding="utf-8") as f:
            alert_json = json.load(f)
    except Exception as e:
        print(f"Error reading alert file {alert_file_path}: {e}", file=sys.stderr)
        sys.exit(1)

    data = json.dumps(alert_json).encode("utf-8")
    req = urllib.request.Request(
        hook_url,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "Wazuh-Integration/4.14"}
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            response_body = response.read().decode("utf-8")
            print(f"Successfully sent alert to {hook_url}: HTTP {response.status}")
    except urllib.error.URLError as e:
        print(f"Failed to post alert to {hook_url}: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
