param(
    [switch] $OpenBrowser
)
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $ProjectRoot "server"
$ClientDir = Join-Path $ProjectRoot "client"
$PythonExe = Join-Path $ServerDir ".venv\Scripts\python.exe"
$ApiUrl = "http://127.0.0.1:8080"
$FrontendPort = 5500

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "The project environment is missing. Run: cd server; python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt"
}

function Test-Port([int] $Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

function Test-ApiReady {
    try {
        $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 2
        return $health.status -eq "healthy"
    } catch {
        return $false
    }
}

if (-not (Test-Port 8080) -and -not (Test-ApiReady)) {
    Start-Process -FilePath $PythonExe `
        -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8080" `
        -WorkingDirectory $ServerDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $ServerDir "uvicorn.out.log") `
        -RedirectStandardError (Join-Path $ServerDir "uvicorn.err.log")
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    if (Test-ApiReady) {
        $ready = $true
        break
    }
    Start-Sleep -Milliseconds 500
}
if (-not $ready) {
    throw "Quoria API did not become ready. Check server\uvicorn.err.log."
}

function Test-QuoriaFrontend([int] $Port) {
    try {
        $page = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/" -TimeoutSec 2
        return $page.Content -match "Quoria|quoria_logo"
    } catch {
        return $false
    }
}

if (-not (Test-QuoriaFrontend $FrontendPort)) {
    # Live Server or another development server may already own 5500. Use the
    # next local port so the user always opens the Quoria frontend.
    $FrontendPort = 5501
}
$SiteUrl = "http://127.0.0.1:$FrontendPort"

if (-not (Test-Port $FrontendPort)) {
    Start-Process -FilePath $PythonExe `
        -ArgumentList "-m http.server $FrontendPort --bind 127.0.0.1" `
        -WorkingDirectory $ClientDir `
        -WindowStyle Hidden
}

if ($OpenBrowser) {
    # Start-Process treats a URL as an executable on some Windows setups.
    # explorer.exe delegates the URL to the user's default browser reliably.
    Start-Process -FilePath "explorer.exe" -ArgumentList $SiteUrl
}
Write-Host "Quoria is ready at $SiteUrl"
