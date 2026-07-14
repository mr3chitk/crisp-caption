@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "CRISPASR_VERSION=v0.8.10"
set "CRISPASR_URL=https://github.com/CrispStrobe/CrispASR/releases/download/v0.8.10/crispasr-windows-x86_64-vulkan.zip"
set "CRISPASR_SHA256=3e90ca3499e7e284af6952c8cdd0c41ead39f805be1a064d29eaefa40175656f"
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
