param(
    [string]$In,
    [string]$Out
)
$ErrorActionPreference = 'Stop'
$app = New-Object -ComObject PowerPoint.Application
try {
    $pres = $app.Presentations.Open($In, $true, $false, $false)
    $pres.SaveAs($Out, 32)   # ppSaveAsPDF
    $pres.Close()
    "OK $([IO.Path]::GetFileName($Out))"
}
finally {
    $app.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
