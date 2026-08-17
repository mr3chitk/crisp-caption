param(
  [Parameter(Mandatory=$true)]$inputFile,
  [Parameter(Mandatory=$true)]$outputFile
)

$content = Get-Content -LiteralPath $inputFile -Raw
$content = $content -replace "`r?`n", ','          # replace newlines with commas
Set-Content -LiteralPath $outputFile -Value $content -NoNewline
