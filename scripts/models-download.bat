@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"
echo Downloading models listed in models\manifest.json...
if exist "%PY%" (
  "%PY%" scripts\download_file.py manifest --manifest models\manifest.json
) else (
  py -3 scripts\download_file.py manifest --manifest models\manifest.json
  if errorlevel 1 python scripts\download_file.py manifest --manifest models\manifest.json
)

if errorlevel 1 (
  echo [FAIL] Model download failed.
  pause
  exit /b 1
)

echo [OK] Models downloaded.
pause
