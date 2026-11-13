$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Launcher = Join-Path $ProjectRoot "start-studyspace.ps1"
$TaskName = "Quoria services"
$PowerShell = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
if (-not (Test-Path -LiteralPath $PowerShell)) {
    $PowerShell = (Get-Command powershell.exe -ErrorAction Stop).Source
}
$Action = New-ScheduledTaskAction -Execute $PowerShell -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Launcher`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Limited

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Description "Starts the local Quoria API and frontend when I sign in." -Force | Out-Null
Start-ScheduledTask -TaskName $TaskName
Write-Host "Quoria will start automatically when you sign in as $env:USERNAME."
Write-Host "To open it now: powershell -ExecutionPolicy Bypass -File `"$Launcher`" -OpenBrowser"
