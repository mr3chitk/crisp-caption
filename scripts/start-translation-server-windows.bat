@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_SERVER=tools\llama.cpp\llama-server.exe"
set "MODEL=models\translation\gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
set "MMPROJ=models\translation\gemma-4-E4B-it-qat-mmproj-F16.gguf"
set "DRAFT=models\translation\mtp-gemma-4-E4B-it-Q8_0.gguf"

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
  -mm "%MMPROJ%" ^
  --no-mmproj-offload ^
  -a Translator ^
  -ngl all ^
  -c 4096 ^
  -b 2048 ^
  -ub 512 ^
  -np -1 ^
  -fa auto ^
  --cache-prompt ^
  --cache-ram 1024 ^
  --cache-reuse 64 ^
  --ctx-checkpoints 0 ^
  --ui-config-file .\ui-configs.json ^
  --cache-type-k q8_0 ^
  --cache-type-v q8_0 ^
  --mlock ^
  --model-draft "%DRAFT%" --spec-type draft-mtp --spec-draft-n-max 2 ^
  --offline ^
  --host 127.0.0.1 ^
  --port 8080
  :: ENABLE THIS FOR TRANSLATEGEMMA --no-jinja ^
pause
