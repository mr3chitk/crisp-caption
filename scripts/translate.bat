@echo off
setlocal
cd /d "%~dp0\.."

set "LLAMA_CLI=tools\llama.cpp\llama-cli.exe"
set "MODEL=models\translation\Hy-MT2-1.8B-UD-Q6_K_XL.gguf"

if not exist "%LLAMA_CLI%" (
  echo [FAIL] llama-cli not found: %LLAMA_CLI%
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

for /f "delims=" %%i in ('powershell -sta "add-type -as System.Windows.Forms; [windows.forms.clipboard]::GetText()"') do Set "text=%%i"
echo "ORIGIN: %text%\n"
set "PROMPT=Translate the following segment to English. Output only the English translation, no extra commentary:\n\n%text%"
"%LLAMA_CLI%" -m "%MODEL%" -p "%PROMPT%" --temp 0.0 -c 4096 --single-turn

pause
