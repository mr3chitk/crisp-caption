@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_SERVER=tools\llama.cpp\llama-server.exe"
set "MODEL=models\translation\Hy-MT2-1.8B-UD-Q6_K_XL.gguf"

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
  -a Hy-MT2-1.8B ^
  -ngl all ^
  -c 4096 ^
  -b 2048 ^
  -ub 512 ^
  -np 1 ^
  --cache-prompt ^
  --cache-reuse 64 ^
  --host 127.0.0.1 ^
  --port 8080

pause
