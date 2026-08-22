@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "LLAMA_CPP_ZIP=tools\cache\llama-cpp-windows.zip"
set "LLAMA_CPP_DIR=tools\llama.cpp"
set "DEST=%~1"
if not defined DEST set "DEST=%CD%"
set "ASSET_PATTERN=%~2"
if not defined ASSET_PATTERN set "ASSET_PATTERN=llama-*-bin-win-cuda-12.4-x64.zip"
set "RELEASES_URL=%~3"
if not defined RELEASES_URL set "RELEASES_URL=https://api.github.com/repos/ggml-org/llama.cpp/releases"

echo Downloading llama.cpp runtime...

powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command ^
   "$ErrorActionPreference = 'Stop';" ^
   "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12;" ^
   "$out = Join-Path $env:DEST $env:LLAMA_CPP_ZIP;" ^
   "$parentDir = Split-Path -Parent $out;" ^
   "New-Item -Path $parentDir -ItemType Directory -Force | Out-Null;" ^
   "$pattern = $env:ASSET_PATTERN;" ^
   "$baseUrl = $env:RELEASES_URL;" ^
   "$headers = @{'User-Agent' = 'llama-cpp-downloader'};" ^
   "$found = $null;" ^
   "for ($page = 1; $page -le 100 -and -not $found; $page++) {" ^
       "Write-Host ('Checking releases page {0}...' -f $page);" ^
       "$separator = if ($baseUrl -match '\?') { '&' } else { '?' };" ^
       "$url = $baseUrl + $separator + 'per_page=100&page=' + $page;" ^
       "$releases = Invoke-RestMethod -Uri $url -Headers $headers;" ^
       "if (-not $releases -or $releases.Count -eq 0) { break };" ^
       "foreach ($release in $releases) {foreach ($asset in @($release.assets)) {if ($asset.name -like $pattern) { $found = $asset; $tag = $release.tag_name; break }} if ($found) { break } } " ^
   "}" ^
   "if (-not $found) {" ^
       "throw ('No release asset matched pattern: {0}' -f $pattern)" ^
   "}" ^
   "Write-Host ('Selected release: {0}' -f $tag);" ^
   "Write-Host ('Downloading: {0}' -f $found.name);" ^
   "Invoke-WebRequest -Uri $found.browser_download_url -Headers $headers -OutFile $out;" ^
   "Write-Host ('Saved to: {0}' -f $out)"

if errorlevel 1 (
    echo Download failed.
    exit /b 1
)

echo Extracting llama.cpp to %LLAMA_CPP_DIR%...
"%PY%" scripts\download_file.py extract --archive "%LLAMA_CPP_ZIP%" --dest "%LLAMA_CPP_DIR%" --strip-top-level --delete-archive
if errorlevel 1 (
  echo [FAIL] llama.cpp extract failed.
  pause
  exit /b 1
)

if not exist "%LLAMA_CPP_DIR%\llama-server.exe" (
  echo [FAIL] llama-server.exe was not found after extraction: %LLAMA_CPP_DIR%\llama-server.exe
  echo Check the zip layout or edit this BAT file.
  pause
  exit /b 1
)

"%LLAMA_CPP_DIR%\llama-server.exe" --help >nul
echo [OK] llama.cpp installed at %LLAMA_CPP_DIR%
pause
