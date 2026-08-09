@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "LLAMA_CPP_VERSION=b10326"
set "LLAMA_CPP_URL=https://github.com/ggml-org/llama.cpp/releases/download/b10326/llama-b10326-bin-win-cuda-12.4-x64.zip"
set "LLAMA_CPP_SHA256=62b4cb0d65ce95561f23d662bd7e5a568f462e24254b24b5b4f8c9e71ea692a7"
set "LLAMA_CPP_ZIP=tools\cache\llama-cpp-windows.zip"
set "LLAMA_CPP_DIR=tools\llama.cpp"

echo Downloading llama.cpp runtime...
if exist "%PY%" (
  "%PY%" scripts\download_file.py one --url "%LLAMA_CPP_URL%" --target "%LLAMA_CPP_ZIP%" --sha256 "%LLAMA_CPP_SHA256%"
) else (
  py -3 scripts\download_file.py one --url "%LLAMA_CPP_URL%" --target "%LLAMA_CPP_ZIP%" --sha256 "%LLAMA_CPP_SHA256%"
  if errorlevel 1 python scripts\download_file.py one --url "%LLAMA_CPP_URL%" --target "%LLAMA_CPP_ZIP%" --sha256 "%LLAMA_CPP_SHA256%"
)
if errorlevel 1 (
  echo [FAIL] llama.cpp download failed.
  echo If the release asset name changed, edit LLAMA_CPP_URL in this BAT file.
  pause
  exit /b 1
)

echo Extracting llama.cpp to %LLAMA_CPP_DIR%...
if exist "%PY%" (
  "%PY%" scripts\download_file.py extract --archive "%LLAMA_CPP_ZIP%" --dest "%LLAMA_CPP_DIR%" --strip-top-level --delete-archive
) else (
  py -3 scripts\download_file.py extract --archive "%LLAMA_CPP_ZIP%" --dest "%LLAMA_CPP_DIR%" --strip-top-level --delete-archive
  if errorlevel 1 python scripts\download_file.py extract --archive "%LLAMA_CPP_ZIP%" --dest "%LLAMA_CPP_DIR%" --strip-top-level --delete-archive
)
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
