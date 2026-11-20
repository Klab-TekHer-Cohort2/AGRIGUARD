# =============================================================================
#  AgriGuard Demo - Stop Everything (Windows PowerShell 5.1+)
#  Run from the AGRIGUARD root:  .\deploy\stop-demo.ps1
# =============================================================================

$DEPLOY_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path

function Write-Step($msg) { Write-Host "  -> $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  OK $msg" -ForegroundColor Green  }

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  AgriGuard Demo - Shutdown" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Kill tunnel process by saved PID
$pidFile = Join-Path $DEPLOY_DIR ".tunnel.pid"
if (Test-Path $pidFile) {
    $savedPid = Get-Content $pidFile -ErrorAction SilentlyContinue
    if ($savedPid -and $savedPid -match '^\d+$') {
        try {
            Stop-Process -Id ([int]$savedPid) -Force -ErrorAction SilentlyContinue
            Write-OK "Tunnel process (PID $savedPid) stopped"
        } catch {
            Write-Step "Tunnel PID $savedPid already gone"
        }
    }
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
} else {
    Write-Step "No tunnel PID file found"
}

# Kill any remaining cloudflared or ngrok processes
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Get-Process -Name "ngrok" -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}
Write-OK "Tunnel cleanup done"

# Kill processes by port (3000, 5000, 8000)
$ports = @(3000, 5000, 8000)
foreach ($port in $ports) {
    $lines = & netstat -ano 2>$null | Select-String ":$port\s"
    if ($lines) {
        $line  = $lines | Select-Object -First 1
        $parts = ($line -split '\s+') | Where-Object { $_ -ne "" }
        $pid_  = $parts[-1]
        if ($pid_ -match '^\d+$' -and [int]$pid_ -gt 4) {
            try {
                Stop-Process -Id ([int]$pid_) -Force -ErrorAction SilentlyContinue
                Write-OK "Process on port $port (PID $pid_) stopped"
            } catch {
                Write-Step "Could not stop PID $pid_ on port $port"
            }
        }
    } else {
        Write-Step "Nothing on port $port"
    }
}

# Show last URL
$lastUrlFile = Join-Path $DEPLOY_DIR ".last-url.txt"
if (Test-Path $lastUrlFile) {
    $lastUrl = Get-Content $lastUrlFile -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "  Last public URL was: $lastUrl" -ForegroundColor DarkGray
    Write-Host "  (That link is now dead. Run start-demo.ps1 for a new one.)" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "  All AgriGuard demo processes stopped." -ForegroundColor Green
Write-Host "  To restart: .\deploy\start-demo.ps1" -ForegroundColor Cyan
Write-Host ""
