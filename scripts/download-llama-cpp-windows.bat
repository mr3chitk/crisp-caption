@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "LLAMA_CPP_ZIP=tools\cache\llama-cpp-windows.zip"
set "LLAMA_CPP_DIR=tools\llama.cpp"
set "REPO=ggml-org/llama.cpp"
set "PATTERN=llama-*-bin-win-cuda-12.4-x64.zip"

echo Downloading llama.cpp runtime...
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
  "$out='%CD%\%LLAMA_CPP_ZIP%';" ^
  "$parentDir = Split-Path -Parent $out;" ^
  "New-Item -Path $parentDir -ItemType Directory -Force | Out-Null;" ^
  "Write-Host ('Downloading to: ' + $out);" ^
  "Invoke-WebRequest -UseBasicParsing -Uri $asset.browser_download_url -OutFile $out;"
if errorlevel 1 (
  echo [FAIL] llama.cpp download failed.
  echo If the release asset name changed, edit LLAMA_CPP_URL in this BAT file.
  pause
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
