# Word -> PDF（更新目录域后导出）
param(
    [string]$Docx,
    [string]$Pdf
)
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($Docx, $false, $false)
    # 更新目录与所有域
    if ($doc.TablesOfContents.Count -gt 0) { $doc.TablesOfContents.Item(1).Update() }
    $doc.Fields.Update() | Out-Null
    $doc.Repaginate()
    $pages = $doc.ComputeStatistics(2)   # wdStatisticPages
    $words = $doc.ComputeStatistics(0)   # wdStatisticWords
    $doc.ExportAsFixedFormat($Pdf, 17, $false, 0, 0, 0, 0, 0, $true, $true, 0, $true, $true, $false)
    $doc.Close(0)
    "$([IO.Path]::GetFileName($Pdf))  页数=$pages  字数=$words"
}
finally {
    $word.Quit()
    [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
}
