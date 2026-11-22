$ErrorActionPreference = 'Stop'
$SystemRootPath = Split-Path -Parent $PSScriptRoot
$BundledJdk = Get-ChildItem -LiteralPath (Join-Path $SystemRootPath '.tools') -Directory -Filter 'jdk-21*' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($BundledJdk) { $env:JAVA_HOME = $BundledJdk.FullName }
$MavenExecutable = Join-Path $SystemRootPath '.tools/apache-maven-3.9.9/bin/mvn.cmd'
if (-not (Test-Path -LiteralPath $MavenExecutable)) { $MavenCommand=Get-Command mvn -ErrorAction SilentlyContinue; $MavenExecutable=if($MavenCommand){$MavenCommand.Source}else{''} }
$JavaExecutable = if($env:JAVA_HOME){Join-Path $env:JAVA_HOME 'bin/java.exe'}else{(Get-Command java -ErrorAction Stop).Source}
if (-not (Test-Path -LiteralPath $JavaExecutable)) { throw '请安装 JDK 21 并设置 JAVA_HOME。' }
function Invoke-Checked([string]$Executable, [string[]]$Arguments) {
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "命令失败：$Executable，退出码 $LASTEXITCODE" }
}
