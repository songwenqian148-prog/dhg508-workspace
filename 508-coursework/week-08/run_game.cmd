@echo off
rem 图穷 - open the game. Starts a supervised local server if one is not running.
setlocal
cd /d "%~dp0"
set PORT=8765

powershell -NoProfile -Command "try { $null = Invoke-WebRequest 'http://127.0.0.1:%PORT%/api/health' -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }"
if %errorlevel%==0 (
  echo Server already running on port %PORT%. Opening the game...
  start "" "http://127.0.0.1:%PORT%/"
  exit /b 0
)

echo Starting the server (a minimised window keeps it alive while you play)...
start "TuQiong - server" /min cmd /c serve_forever.cmd
timeout /t 3 >nul
start "" "http://127.0.0.1:%PORT%/"
exit /b 0
