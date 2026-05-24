@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"
if exist "%PY%" (
  "%PY%" scripts\check_deps.py
) else (
  py -3 scripts\check_deps.py
  if errorlevel 1 python scripts\check_deps.py
)
set "STATUS=%ERRORLEVEL%"
pause
exit /b %STATUS%
