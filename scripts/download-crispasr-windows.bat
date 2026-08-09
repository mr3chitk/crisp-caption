@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "CRISPASR_ZIP=tools\cache\crispasr-windows.zip"
set "CRISPASR_DIR=tools\crispasr"
set "REPO=CrispStrobe/CrispASR"
set "PATTERN=crispasr-windows-x86_64-cuda.zip"

echo Downloading CrispASR runtime...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$repo='%REPO%';" ^
  "$pattern='%PATTERN%';" ^
  "$api='https://api.github.com/repos/' + $repo + '/releases/latest';" ^
  "$rel=Invoke-RestMethod -UseBasicParsing $api;" ^
  "$assets=$rel.assets | Where-Object { $_.name -like $pattern } | Sort-Object name -Descending;" ^
  "if(-not $assets){ throw 'No asset matched pattern: ' + $pattern }" ^
  "$asset=$assets | Select-Object -First 1;" ^
  "Write-Host ('Selected asset: ' + $asset.browser_download_url);" ^
  "$out='%CD%\%CRISPASR_ZIP%';" ^
  "$parentDir = Split-Path -Parent $out;" ^
  "New-Item -Path $parentDir -ItemType Directory -Force | Out-Null;" ^
  "Write-Host ('Downloading to: ' + $out);" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $out;"
if errorlevel 1 (
  echo [FAIL] CrispASR download failed.
  echo If the release asset name changed, edit CRISPASR_URL in this BAT file.
  pause
  exit /b 1
)

echo Extracting CrispASR to %CRISPASR_DIR%...
"%PY%" scripts\download_file.py extract --archive "%CRISPASR_ZIP%" --dest "%CRISPASR_DIR%" --strip-top-level --delete-archive
if errorlevel 1 (
  echo [FAIL] CrispASR extract failed.
  pause
  exit /b 1
)

if not exist "%CRISPASR_DIR%\crispasr.exe" (
  echo [FAIL] crispasr.exe was not found after extraction: %CRISPASR_DIR%\crispasr.exe
  echo Check the zip layout or edit this BAT file.
  pause
  exit /b 1
)

"%CRISPASR_DIR%\crispasr.exe" --version
echo [OK] CrispASR installed at %CRISPASR_DIR%
pause
