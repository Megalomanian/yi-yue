$ErrorActionPreference='Stop'
$SystemRootPath=Split-Path -Parent $PSScriptRoot
foreach($Name in @('backend','frontend')) {
    $PidPath=Join-Path $SystemRootPath "data/runtime/$Name.pid"
    if(Test-Path -LiteralPath $PidPath) {
        $ProcessNumber=[int](Get-Content -LiteralPath $PidPath)
        $ProcessInfo=Get-CimInstance Win32_Process -Filter "ProcessId=$ProcessNumber"
        if($ProcessInfo -and $ProcessInfo.CommandLine.Contains($SystemRootPath)) { Stop-Process -Id $ProcessNumber }
        Remove-Item -LiteralPath $PidPath
    }
}
Write-Output '仪约本地进程已停止，数据已保留。'
