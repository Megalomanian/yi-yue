param(
    [string]$DocxDir,
    [string]$PdfDir
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $PdfDir)) { New-Item -ItemType Directory -Force -Path $PdfDir | Out-Null }
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    Get-ChildItem -Path $DocxDir -Filter *.docx | ForEach-Object {
        $doc = $word.Documents.Open($_.FullName, $false, $false)
        $doc.Fields.Update() | Out-Null
        $doc.Repaginate()
        $pages = $doc.ComputeStatistics(2)
        $pdf = Join-Path $PdfDir ($_.BaseName + '.pdf')
        $doc.ExportAsFixedFormat($pdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 0, $true, $true, $false)
        $doc.Close(0)
        "{0}  页数={1}" -f $_.BaseName, $pages
    }
}
finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
