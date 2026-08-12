@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_SERVER=tools\llama.cpp\llama-server.exe"
set "MODEL=models\translation\gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"

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
  --model-draft "models\translation\mtp-gemma-4-E4B-it-Q4_0.gguf" --spec-type draft-mtp --spec-draft-n-max 2 ^
  -a Translator ^
  -ngl all ^
  -c 2048 ^
  -b 1024 ^
  -ub 512 ^
  -np 1 ^
  -fa auto ^
  --no-mmproj-offload ^
  --kv-unified ^
  --cache-prompt ^
  --cache-ram 1024 ^
  --ui-config-file .\ui-configs.json ^
  --load-mode mlock ^
  --offline ^
  --reasoning off ^
  --reasoning-budget 0 ^
  --seed 1 ^
  --host 127.0.0.1 --port 8080
pause
