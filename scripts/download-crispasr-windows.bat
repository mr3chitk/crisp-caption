@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "CRISPASR_VERSION=v0.8.9"
set "CRISPASR_URL=https://github.com/CrispStrobe/CrispASR/releases/download/v0.8.9/crispasr-windows-x86_64-vulkan.zip"
set "CRISPASR_SHA256=39b803fce62e534215e210a214376996754f0d5c9827cd5ba9cfd230084a5aff"
set "CRISPASR_ZIP=tools\cache\crispasr-windows-vulkan.zip"
set "CRISPASR_DIR=tools\crispasr"

echo Downloading CrispASR Vulkan runtime...
if exist "%PY%" (
  "%PY%" scripts\download_file.py one --url "%CRISPASR_URL%" --target "%CRISPASR_ZIP%" --sha256 "%CRISPASR_SHA256%"
) else (
  py -3 scripts\download_file.py one --url "%CRISPASR_URL%" --target "%CRISPASR_ZIP%" --sha256 "%CRISPASR_SHA256%"
  if errorlevel 1 python scripts\download_file.py one --url "%CRISPASR_URL%" --target "%CRISPASR_ZIP%" --sha256 "%CRISPASR_SHA256%"
)
if errorlevel 1 (
  echo [FAIL] CrispASR download failed.
  echo If the release asset name changed, edit CRISPASR_URL in this BAT file.
  pause
  exit /b 1
)

echo Extracting CrispASR to %CRISPASR_DIR%...
if exist "%PY%" (
  "%PY%" scripts\download_file.py extract --archive "%CRISPASR_ZIP%" --dest "%CRISPASR_DIR%" --strip-top-level --delete-archive
) else (
  py -3 scripts\download_file.py extract --archive "%CRISPASR_ZIP%" --dest "%CRISPASR_DIR%" --strip-top-level --delete-archive
  if errorlevel 1 python scripts\download_file.py extract --archive "%CRISPASR_ZIP%" --dest "%CRISPASR_DIR%" --strip-top-level --delete-archive
)
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
