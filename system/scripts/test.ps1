. "$PSScriptRoot/environment.ps1"
& "$PSScriptRoot/build.ps1"
& "$PSScriptRoot/stop.ps1"
& "$PSScriptRoot/start.ps1"
Push-Location (Join-Path $SystemRootPath 'frontend')
try { Invoke-Checked 'npm.cmd' @('run','test:e2e') } finally { Pop-Location }
