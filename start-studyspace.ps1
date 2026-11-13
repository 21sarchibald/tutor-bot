param(
    [switch] $OpenBrowser
)
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ServerDir = Join-Path $ProjectRoot "server"
$ClientDir = Join-Path $ProjectRoot "client"
$PythonExe = Join-Path $ServerDir ".venv\Scripts\python.exe"
$ApiUrl = "http://127.0.0.1:8080"
$SiteUrl = "http://127.0.0.1:5500"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "The project environment is missing. Run: cd server; python -m venv .venv; .venv\Scripts\python.exe -m pip install -r requirements.txt"
}

function Test-Port([int] $Port) {
    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    return $null -ne $connection
}

if (-not (Test-Port 8080)) {
    Start-Process -FilePath $PythonExe `
        -ArgumentList "-m uvicorn main:app --host 127.0.0.1 --port 8080" `
        -WorkingDirectory $ServerDir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $ServerDir "uvicorn.out.log") `
        -RedirectStandardError (Join-Path $ServerDir "uvicorn.err.log")
}

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod -Uri "$ApiUrl/health" -TimeoutSec 2
        if ($health.status -eq "healthy") {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}
if (-not $ready) {
    throw "Quoria API did not become ready. Check server\uvicorn.err.log."
}

if (-not (Test-Port 5500)) {
    Start-Process -FilePath $PythonExe `
        -ArgumentList "-m http.server 5500 --bind 127.0.0.1" `
        -WorkingDirectory $ClientDir `
        -WindowStyle Hidden
}

if ($OpenBrowser) {
    Start-Process $SiteUrl
}
Write-Host "Quoria is ready at $SiteUrl"
