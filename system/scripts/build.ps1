. "$PSScriptRoot/environment.ps1"
if(-not $MavenExecutable){throw '构建需要 Maven 3.9，请安装并加入 PATH。'}
Push-Location (Join-Path $SystemRootPath 'backend')
try { Invoke-Checked $MavenExecutable @('-s','../maven-settings.xml','-B','-ntp','verify') } finally { Pop-Location }
Push-Location (Join-Path $SystemRootPath 'frontend')
try { Invoke-Checked 'npm.cmd' @('ci','--no-fund','--no-audit'); Invoke-Checked 'npm.cmd' @('test'); Invoke-Checked 'npm.cmd' @('run','build') } finally { Pop-Location }
