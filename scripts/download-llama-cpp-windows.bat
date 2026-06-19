@echo off
setlocal
cd /d "%~dp0\.."

set "PY=%CD%\.venv\Scripts\python.exe"

set "LLAMA_CPP_VERSION=b9724"
set "LLAMA_CPP_URL=https://github.com/ggml-org/llama.cpp/releases/download/b9724/llama-b9724-bin-win-cuda-12.4-x64.zip"
set "LLAMA_CPP_SHA256=913d47f80a3cad43fe95eda2ed0cf0dbd5fe01d758f66c097fa0a6138021729d"
set "LLAMA_CPP_ZIP=tools\cache\llama-cpp-windows-vulkan.zip"
set "LLAMA_CPP_DIR=tools\llama.cpp"

echo Downloading llama.cpp Vulkan runtime...
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
