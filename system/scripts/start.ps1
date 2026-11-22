. "$PSScriptRoot/environment.ps1"
$JarPath = Join-Path $SystemRootPath 'backend/target/instrumenthub-1.0.0.jar'
if (-not (Test-Path -LiteralPath $JarPath)) { & "$PSScriptRoot/build.ps1" }
$RuntimePath = Join-Path $SystemRootPath 'data/runtime'
New-Item -ItemType Directory -Force $RuntimePath | Out-Null
foreach ($ListenPort in @(8080,5173)) { if (Get-NetTCPConnection -LocalPort $ListenPort -State Listen -ErrorAction SilentlyContinue) { throw "端口 $ListenPort 已被使用。若仪约已启动，可直接打开 http://localhost:5173。" } }
$RunJarPath=Join-Path $RuntimePath 'instrumenthub.jar'
Copy-Item -LiteralPath $JarPath -Destination $RunJarPath -Force
$BackendProcess = Start-Process -FilePath $JavaExecutable -ArgumentList @('-jar',"`"$RunJarPath`"") -WorkingDirectory (Join-Path $SystemRootPath 'backend') -RedirectStandardOutput (Join-Path $RuntimePath 'backend.log') -RedirectStandardError (Join-Path $RuntimePath 'backend-error.log') -WindowStyle Hidden -PassThru
$BackendProcess.Id | Set-Content (Join-Path $RuntimePath 'backend.pid')
$VitePath = Join-Path $SystemRootPath 'frontend/node_modules/vite/bin/vite.js'
$FrontendProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList @("`"$VitePath`"",'--host','127.0.0.1') -WorkingDirectory (Join-Path $SystemRootPath 'frontend') -RedirectStandardOutput (Join-Path $RuntimePath 'frontend.log') -RedirectStandardError (Join-Path $RuntimePath 'frontend-error.log') -WindowStyle Hidden -PassThru
$FrontendProcess.Id | Set-Content (Join-Path $RuntimePath 'frontend.pid')
$Ready=$false
for($Attempt=0;$Attempt -lt 30;$Attempt++) {
    try { $Health=Invoke-RestMethod 'http://127.0.0.1:8080/actuator/health' -TimeoutSec 1; if($Health.status -eq 'UP'){$Ready=$true;break} } catch {}
    Start-Sleep -Seconds 1
}
if(-not $Ready){throw "后端未通过健康检查，请查看 $RuntimePath/backend.log"}
Write-Output '已启动并通过健康检查：前端 http://localhost:5173 ，后端 http://localhost:8080 。'
