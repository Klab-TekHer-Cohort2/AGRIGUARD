# =============================================================================
#  AgriGuard Demo - Start Everything (Windows PowerShell 5.1+)
#  Run from the AGRIGUARD root:  .\deploy\start-demo.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

$SCRIPT_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT        = Split-Path -Parent $SCRIPT_DIR
$BACKEND_DIR = Join-Path $ROOT "backend"
$DEPLOY_DIR  = $SCRIPT_DIR

$BACKEND_PORT = 8000
$AI_PORT      = 5000
$PROXY_PORT   = 3000

function Write-Header($msg) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}

function Write-Step($msg) { Write-Host "  -> $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  OK $msg" -ForegroundColor Green  }
function Write-Fail($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red  }

function Wait-For-HTTP($uri, $label) {
    Write-Step "Waiting for $label at $uri ..."
    for ($i = 1; $i -le 20; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $uri -UseBasicParsing -TimeoutSec 4 -ErrorAction Stop
            if ($r.StatusCode -lt 500) {
                Write-OK "$label is up (HTTP $($r.StatusCode))"
                return $true
            }
        } catch { }
        Write-Host "    attempt $i/20 - retrying in 3s ..." -ForegroundColor DarkGray
        Start-Sleep -Seconds 3
    }
    Write-Fail "$label did not respond after 60 seconds."
    return $false
}

# ---------------------------------------------------------------------------
Write-Header "AgriGuard Demo Launcher - Windows PowerShell"
Write-Host "  Root: $ROOT" -ForegroundColor DarkGray

# ---------------------------------------------------------------------------
Write-Header "Step 1 - Checking tools"

try {
    $pyVer = & python --version 2>&1
    Write-OK "Python: $pyVer"
} catch {
    Write-Fail "Python not found. Install from https://python.org and retry."
    exit 1
}

try {
    $nodeVer = & node --version 2>&1
    Write-OK "Node.js: $nodeVer"
} catch {
    Write-Fail "Node.js not found. Install from https://nodejs.org and retry."
    exit 1
}

# Find cloudflared - check PATH, then deploy/, then try to download
$cloudflaredCmd = $null
$useTunnel = "cloudflared"

$cfInPath = Get-Command cloudflared -ErrorAction SilentlyContinue
$cfExe    = Join-Path $DEPLOY_DIR "cloudflared.exe"

if ($cfInPath) {
    $cloudflaredCmd = "cloudflared"
    Write-OK "cloudflared found: $($cfInPath.Source)"
} elseif (Test-Path $cfExe) {
    $cloudflaredCmd = $cfExe
    Write-OK "cloudflared.exe found in deploy/"
} else {
    Write-Step "cloudflared not in PATH - downloading portable exe ..."
    try {
        $cfUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
        Invoke-WebRequest -Uri $cfUrl -OutFile $cfExe -UseBasicParsing -TimeoutSec 90
        $cloudflaredCmd = $cfExe
        Write-OK "Downloaded cloudflared.exe to deploy/"
    } catch {
        Write-Host "  WARNING: Could not download cloudflared. Trying ngrok fallback." -ForegroundColor DarkYellow
        $useTunnel = "ngrok"
        $ngrokInPath = Get-Command ngrok -ErrorAction SilentlyContinue
        if (-not $ngrokInPath) {
            Write-Fail "Neither cloudflared nor ngrok found."
            Write-Host ""
            Write-Host "  OPTION A - cloudflared (no account needed):" -ForegroundColor Yellow
            Write-Host "    1. Download cloudflared-windows-amd64.exe from:" -ForegroundColor White
            Write-Host "       https://github.com/cloudflare/cloudflared/releases/latest" -ForegroundColor White
            Write-Host "    2. Save it as: $cfExe" -ForegroundColor White
            Write-Host "    3. Re-run this script." -ForegroundColor White
            Write-Host ""
            Write-Host "  OPTION B - ngrok (free account required):" -ForegroundColor Yellow
            Write-Host "    1. Sign up at https://ngrok.com" -ForegroundColor White
            Write-Host "    2. Download ngrok.exe and add it to your PATH" -ForegroundColor White
            Write-Host "    3. Run: ngrok config add-authtoken YOUR_TOKEN" -ForegroundColor White
            Write-Host "    4. Re-run this script." -ForegroundColor White
            Write-Host ""
            exit 1
        }
        Write-OK "ngrok found: $($ngrokInPath.Source)"
    }
}

# ---------------------------------------------------------------------------
Write-Header "Step 2 - Installing Python dependencies"

Write-Step "Backend requirements ..."
Push-Location $BACKEND_DIR
& python -m pip install -r requirements.txt -q --disable-pip-version-check 2>&1 | Where-Object { $_ -match "ERROR|error" } | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
if ($LASTEXITCODE -ne 0) {
    Write-Fail "pip install failed for backend (exit $LASTEXITCODE). Run manually to see errors:"
    Write-Host "  cd backend; python -m pip install -r requirements.txt" -ForegroundColor Yellow
    Pop-Location; exit 1
}
Write-OK "Backend requirements installed"
Pop-Location

Write-Step "AI service requirements ..."
Push-Location $ROOT
& python -m pip install -r requirements.txt -q --disable-pip-version-check 2>&1 | Where-Object { $_ -match "ERROR|error" } | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkYellow }
if ($LASTEXITCODE -ne 0) {
    Write-Fail "pip install failed for AI service (exit $LASTEXITCODE). Run manually to see errors:"
    Write-Host "  python -m pip install -r requirements.txt" -ForegroundColor Yellow
    Pop-Location; exit 1
}
Write-OK "AI service requirements installed"
Pop-Location

# ---------------------------------------------------------------------------
Write-Header "Step 3 - Starting backend FastAPI (port $BACKEND_PORT)"

$backendEnv = Join-Path $BACKEND_DIR ".env"
if (-not (Test-Path $backendEnv)) {
    Copy-Item (Join-Path $BACKEND_DIR ".env.example") $backendEnv
    Write-Step "Created backend/.env from .env.example"
}

$backendCmd = "Set-Location '$BACKEND_DIR'; python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT; Write-Host 'Backend stopped. Press Enter to close.'; Read-Host"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# ---------------------------------------------------------------------------
Write-Header "Step 4 - Starting AI service FastAPI (port $AI_PORT)"

$aiEnv = Join-Path $ROOT ".env"
if (-not (Test-Path $aiEnv)) {
    Copy-Item (Join-Path $ROOT ".env.example") $aiEnv
    Write-Step "Created .env from .env.example"
}

$aiCmd = "Set-Location '$ROOT'; python -m uvicorn app.main:app --host 0.0.0.0 --port $AI_PORT; Write-Host 'AI service stopped. Press Enter to close.'; Read-Host"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $aiCmd

# ---------------------------------------------------------------------------
Write-Header "Step 5 - Starting Node proxy (port $PROXY_PORT)"

$proxyCmd = "Set-Location '$DEPLOY_DIR'; node proxy.js; Write-Host 'Proxy stopped. Press Enter to close.'; Read-Host"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $proxyCmd

# ---------------------------------------------------------------------------
Write-Header "Step 6 - Health checks (waiting for services to start ...)"

Start-Sleep -Seconds 15

$backendOk = Wait-For-HTTP "http://localhost:$BACKEND_PORT/health"    "Backend"  30 4
$aiOk      = Wait-For-HTTP "http://localhost:$AI_PORT/health"         "AI service" 30 4
$proxyOk   = Wait-For-HTTP "http://localhost:$PROXY_PORT/proxy-health" "Proxy"    15 2

if (-not $backendOk) {
    Write-Host ""
    Write-Fail "Backend did not start. Check the backend PowerShell window for errors."
    Write-Host "  Common fix: run  pip install -r backend\requirements.txt  manually." -ForegroundColor Yellow
    exit 1
}
if (-not $aiOk) {
    Write-Host ""
    Write-Fail "AI service did not start. Check the AI PowerShell window for errors."
    Write-Host "  Common fix: run  pip install -r requirements.txt  manually." -ForegroundColor Yellow
    exit 1
}
if (-not $proxyOk) {
    Write-Host ""
    Write-Fail "Proxy did not start. Check the proxy PowerShell window for errors."
    exit 1
}

# ---------------------------------------------------------------------------
Write-Header "Step 7 - Starting public tunnel"

$tunnelLog = Join-Path $DEPLOY_DIR "tunnel.log"
if (Test-Path $tunnelLog) { Remove-Item $tunnelLog -Force }

if ($useTunnel -eq "cloudflared") {
    Write-Step "Starting Cloudflare Quick Tunnel (no account needed) ..."

    $tunnelProc = Start-Process -FilePath $cloudflaredCmd `
        -ArgumentList "tunnel", "--url", "http://localhost:$PROXY_PORT", "--no-autoupdate" `
        -RedirectStandardError $tunnelLog `
        -PassThru -WindowStyle Hidden

    $tunnelProc.Id | Out-File (Join-Path $DEPLOY_DIR ".tunnel.pid") -Encoding ascii

    Write-Step "Waiting for tunnel URL (up to 40 seconds) ..."
    $publicUrl = $null
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $tunnelLog) {
            $logText = [IO.File]::ReadAllText($tunnelLog)
            if ($logText -match 'https://[a-z0-9\-]+\.trycloudflare\.com') {
                $publicUrl = $Matches[0]
                break
            }
        }
    }

    if (-not $publicUrl) {
        Write-Fail "Could not read tunnel URL. Check: $tunnelLog"
        Write-Host "  You can still access the app locally at: http://localhost:$PROXY_PORT" -ForegroundColor Yellow
        exit 1
    }

} else {
    Write-Step "Starting ngrok tunnel ..."
    $ngrokProc = Start-Process ngrok -ArgumentList "http", $PROXY_PORT -PassThru -WindowStyle Hidden
    $ngrokProc.Id | Out-File (Join-Path $DEPLOY_DIR ".tunnel.pid") -Encoding ascii
    Start-Sleep -Seconds 4
    try {
        $ngrokApi  = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels" -TimeoutSec 10
        $publicUrl = ($ngrokApi.tunnels | Where-Object { $_.proto -eq "https" })[0].public_url
    } catch {
        Write-Fail "Could not read ngrok tunnel URL. Check http://localhost:4040"
        exit 1
    }
}

# ---------------------------------------------------------------------------
Write-Header "AgriGuard is LIVE!"

Write-Host ""
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Green
Write-Host "  |                                                          |" -ForegroundColor Green
Write-Host "  |  PUBLIC LINK:" -ForegroundColor Green -NoNewline
Write-Host "  $publicUrl" -ForegroundColor White
Write-Host "  |                                                          |" -ForegroundColor Green
Write-Host "  +----------------------------------------------------------+" -ForegroundColor Green
Write-Host ""
Write-Host "  Local (this laptop only):" -ForegroundColor DarkGray
Write-Host "    App       -> http://localhost:$PROXY_PORT" -ForegroundColor DarkGray
Write-Host "    Backend   -> http://localhost:$BACKEND_PORT/docs" -ForegroundColor DarkGray
Write-Host "    AI service-> http://localhost:$AI_PORT/docs" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Share the PUBLIC LINK above with your audience." -ForegroundColor Cyan
Write-Host "  To stop everything: .\deploy\stop-demo.ps1" -ForegroundColor Cyan
Write-Host ""

$publicUrl | Out-File (Join-Path $DEPLOY_DIR ".last-url.txt") -Encoding ascii
