# OCR whatever image is currently in the Windows clipboard, then copy the recognized text back to the clipboard.
# TIP: You can setup AutoHotkey v2 for fast screenshot + ocr shortcuts.
<#
    #SingleInstance Force
    Pause::
	{
		ps1 := "C:\Users\PC\crisp-caption\scripts\ocr-clipboard.ps1"
		cmd := 'powershell.exe -NoProfile -ExecutionPolicy Bypass -File "' ps1 '"'
		Run(cmd, , "Min")
	}
#>

$ErrorActionPreference = "Stop"

# 1) Read the clipboard image
$img = Get-Clipboard -Format Image
if (-not $img) { throw "Clipboard does not contain an image." }

# 2) Save image to a temp PNG file
Add-Type -AssemblyName System.Drawing
$tempPng = Join-Path $env:TEMP ("clip_ocr_{0}.png" -f ([Guid]::NewGuid().ToString("N")))
$img.Save($tempPng)

# markdown cleaner
function ConvertFrom-Markdown {
    param([string]$Text)
    
    # Remove markdown links [text](url) -> text
    $Text = $Text -replace '\[([^\]]+)\]\([^\)]+\)', '$1'
    
    # Remove markdown images ![alt](url)
    $Text = $Text -replace '!\[([^\]]*)\]\([^\)]+\)', '$1'
    
    # Remove bold/italic **text** or __text__ -> text
    $Text = $Text -replace '(\*\*|__)(.*?)\1', '$2'
    
    # Remove italic *text* or _text_ -> text
    $Text = $Text -replace '(\*|_)(.*?)\1', '$2'
    
    # Remove inline code `text` -> text
    $Text = $Text -replace '`([^`]+)`', '$1'
    
    # Remove headers (#, ##, etc.)
    $Text = $Text -replace '^#+\s+', ''
    
    # Remove horizontal rules (---, ***, ___)
    $Text = $Text -replace '^\s*(---|===|___)\s*$', ''
    
    # Remove blockquotes (>)
    $Text = $Text -replace '^\s*>\s+', ''
    
    # Remove strikethrough ~~text~~ -> text
    $Text = $Text -replace '~~([^~]+)~~', '$1'
    
    # ARTIFACT: Remove <think> tags and content
    $Text = $Text -replace '<think>[\s\S]*?</think>', ''
    return $Text.Trim()
}

# 3) Run OCR client
$parent = Split-Path -Parent $MyInvocation.MyCommand.Path
$parent = Split-Path -Parent $parent
try {
    # INFO: if you have extra VRAM, you can disable "--device","none" 
    $exe = "${parent}\tools\llama.cpp\llama-mtmd-cli.exe"
    $args = @(
		"-m","${parent}\models\ocr\OvisOCR2-Q8_0.gguf",
		"--mmproj","${parent}\models\ocr\OvisOCR2-mmproj-BF16.gguf",
        "--image", $tempPng,
		"-p", "<|im_start|>user\nExtract all readable content from the image in natural human reading order and output the result as a single Markdown document. Format formulas as LaTeX. Format tables as HTML: <table>...</table>. Preserve the original text without translation.<|im_end|>\n<|im_start|>assistant\n",
		"-n","4096",
		"--temp","0.0",
        "--offline",
        "--device","none"
    )
    # Capture whatever .exe prints and treat it as OCR text.
    $ocrText = (& $exe @args | Out-String).Trim()
    $plain = ConvertFrom-Markdown -Text $ocrText 
    if (-not $plain) { throw "OCR client returned empty text." }

    # 4) Copy OCR text back to clipboard
    Set-Clipboard -Value $plain
    Write-Host "OCR text copied to clipboard."
}
finally {
    Remove-Item $tempPng -Force -ErrorAction SilentlyContinue
}
