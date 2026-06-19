@echo off
setlocal
cd /d "%~dp0\.."

echo Building browser UI...
pushd frontend

call npm run build
if errorlevel 1 (
  popd
  goto fail
)
popd

echo.
echo [OK] Setup completed.
pause
exit /b 0

:fail
echo [FAIL] Setup failed.
pause
exit /b 1