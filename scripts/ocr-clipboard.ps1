# OCR whatever image is currently in the Windows clipboard, then copy the recognized text back to the clipboard.

$ErrorActionPreference = "Stop"

# 1) Read the clipboard image
$img = Get-Clipboard -Format Image
if (-not $img) { throw "Clipboard does not contain an image." }

# 2) Save image to a temp PNG file
Add-Type -AssemblyName System.Drawing
$tempPng = Join-Path $env:TEMP ("clip_ocr_{0}.png" -f ([Guid]::NewGuid().ToString("N")))
$img.Save($tempPng)

# 3) Run OCR client
$parent = Split-Path -Parent $MyInvocation.MyCommand.Path
$parent = Split-Path -Parent $parent
try {
    $exe = "${parent}\tools\llama.cpp\llama-mtmd-cli.exe"
    $args = @(
		"-m","${parent}\models\ocr\OvisOCR2-Q6_K.gguf",
		"--mmproj","${parent}\models\ocr\OvisOCR2-Q6_K-mmproj-BF16.gguf",
        "--image", $tempPng,
		"-p", "<|im_start|>user\nExtract all readable content from the image in natural human reading order and output the result as a single Markdown document. Format formulas as LaTeX. Format tables as HTML: <table>...</table>. Preserve the original text without translation.<|im_end|>\n<|im_start|>assistant\n",
		"-n","4096",
		"--temp","0.0"
    )

    # Capture whatever .exe prints and treat it as OCR text.
    $ocrText = (& $exe @args | Out-String).Trim()
	$ocrText = [regex]::Replace($ocrText, "<think>.*?</think>", "", "Singleline").Trim()

    if (-not $ocrText) { throw "OCR client returned empty text." }

    # 4) Copy OCR text back to clipboard
    Set-Clipboard -Value $ocrText
    Write-Host "OCR text copied to clipboard."
}
finally {
    Remove-Item $tempPng -Force -ErrorAction SilentlyContinue
}
