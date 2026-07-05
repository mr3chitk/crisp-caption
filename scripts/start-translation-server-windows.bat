@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_SERVER=tools\llama.cpp\llama-server.exe"
set "MODEL=models\translation\Qwen3.5-4B-Q4_K_M.gguf"

if not exist "%LLAMA_SERVER%" (
  echo [FAIL] llama-server not found: %LLAMA_SERVER%
  echo Run scripts\download-llama-cpp-windows.bat first.
  pause
  exit /b 1
)

if not exist "%MODEL%" (
  echo [FAIL] translation model not found: %MODEL%
  echo Run scripts\models-download.bat first.
  pause
  exit /b 1
)

"%LLAMA_SERVER%" ^
  -m "%MODEL%" ^
  -a Translator ^
  -ngl all ^
  -c 4096 ^
  -b 2048 ^
  -ub 512 ^
  -np 1 ^
  -fa auto ^
  --cache-prompt ^
  --cache-ram 1024 ^
  --host 127.0.0.1 ^
  --port 8080
  ::--kv-unified ^
  :: --cache-type-v q8_0 ^
  :: --cache-type-k q8_0 ^
  :: ENABLE THIS FOR MTP --spec-type draft-mtp --spec-draft-n-max 6 ^
  :: ENABLE THIS FOR TRANSLATEGEMMA --no-jinja
pause
