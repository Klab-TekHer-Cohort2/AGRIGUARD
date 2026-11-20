# =============================================================================
#  AgriGuard Demo - Rebuild frontend then Start Everything
#  Use this if you changed frontend code and need a fresh build.
#  Run from the AGRIGUARD root:  .\deploy\rebuild-and-start.ps1
# =============================================================================

$SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Path
$ROOT         = Split-Path -Parent $SCRIPT_DIR
$FRONTEND_DIR = Join-Path $ROOT "frontend"

function Write-Header($msg) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
}
function Write-Step($msg) { Write-Host "  -> $msg" -ForegroundColor Yellow }
function Write-OK($msg)   { Write-Host "  OK $msg" -ForegroundColor Green  }
function Write-Fail($msg) { Write-Host "  FAIL $msg" -ForegroundColor Red  }

Write-Header "Rebuilding Expo web bundle ..."

# Ensure frontend/.env exists with empty URLs (uses proxy relative paths)
$frontendEnv = Join-Path $FRONTEND_DIR ".env"
if (-not (Test-Path $frontendEnv)) {
    "EXPO_PUBLIC_BACKEND_URL=" | Set-Content $frontendEnv -Encoding UTF8
    "EXPO_PUBLIC_AI_URL="      | Add-Content $frontendEnv -Encoding UTF8
    Write-Step "Created frontend/.env with empty URLs (proxy handles routing)"
}

Write-Step "npm install ..."
Push-Location $FRONTEND_DIR
try {
    & npm install --legacy-peer-deps --silent 2>&1 | Out-Null
    Write-OK "npm install done"
} catch {
    Write-Fail "npm install failed: $_"
    Pop-Location; exit 1
}

Write-Step "expo export --platform web --clear ..."
try {
    & npx expo export --platform web --clear 2>&1
    Write-OK "Web build complete -> frontend/dist/"
} catch {
    Write-Fail "Build failed. Check output above."
    Pop-Location; exit 1
}
Pop-Location

Write-Header "Build done - launching demo ..."
& "$SCRIPT_DIR\start-demo.ps1"
