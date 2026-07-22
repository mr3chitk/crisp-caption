@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_SERVER=tools\llama.cpp\llama-server.exe"
set "MODEL=models\translation\gemma-4-E4B-it-qat-UD-Q4_K_XL.gguf"
set "MMPROJ=models\translation\gemma-4-E4B-it-qat-mmproj-BF16.gguf"
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
  -c 2048 ^
  -b 1024 ^
  -ub 512 ^
  -np 2 ^
  -fa auto ^
  --kv-unified ^
  --cache-prompt ^
  --cache-ram 1024 ^
  --cache-type-k q8_0 ^
  --cache-type-v q8_0 ^
  --ctx-checkpoints 16 ^
  --ui-config-file .\ui-configs.json ^
  --mlock ^
  --offline ^
  --model-draft "%DRAFT%" --spec-type draft-mtp --spec-draft-n-max 3 ^
  --host 127.0.0.1 --port 8080
  :: --no-jinja ^
  :: --chat-template-file "models\translation\Qwen3.5-chat_template.jinja" ^
pause
