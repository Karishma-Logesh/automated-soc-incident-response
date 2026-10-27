<#
.SYNOPSIS
    Automated Brute-Force Simulation for Wazuh Rule 100051 Validation.
.DESCRIPTION
    Generates 5 consecutive failed authentication attempts against the local host
    within 120 seconds to trigger Windows Security Event ID 4625 (Logon Failure)
    and validate Wazuh Custom Correlation Rule 100051 (Level 10).
#>

param (
    [string]$TargetUser = "Administrator",
    [int]$Attempts = 5,
    [int]$DelaySeconds = 2
)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Automated SOC Attack Simulation: Credential Brute Force" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[*] Target Host : $env:COMPUTERNAME (Agent 001)" -ForegroundColor Yellow
Write-Host "[*] Target User : $TargetUser" -ForegroundColor Yellow
Write-Host "[*] Total Fails : $Attempts attempts" -ForegroundColor Yellow
Write-Host "[*] Rule Target : Rule ID 100051 (Level 10)" -ForegroundColor Yellow
Write-Host "----------------------------------------------------------"

for ($i = 1; $i -le $Attempts; $i++) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    Write-Host "[$timestamp] [$i/$Attempts] Triggering failed authentication..." -NoNewline -ForegroundColor White
    
    # Net use against local loopback with intentional bad credentials generates Event 4625
    $output = net use \\127.0.0.1 /user:$TargetUser "BadPass_$([guid]::NewGuid().ToString().Substring(0,8))!" 2>&1
    
    Write-Host " [EVENT 4625 GENERATED]" -ForegroundColor Red
    
    if ($i -lt $Attempts) {
        Start-Sleep -Seconds $DelaySeconds
    }
}

Write-Host "----------------------------------------------------------"
Write-Host "[+] Simulation Finished: $Attempts failed logons executed." -ForegroundColor Green
Write-Host "[*] Check Kali terminal to verify Rule 100051 trigger:" -ForegroundColor Cyan
Write-Host "    sudo tail -f /var/ossec/logs/alerts/alerts.log | grep 100051" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
