@echo off
rem Keep the local server alive: if it dies, start it again after 2 seconds.
rem Double-click this once; a minimised window stays open while the game is in use.
setlocal
cd /d "%~dp0"
title 图穷 - local server (keep this window open)

:loop
echo [%date% %time%] starting server on port 8765 ...
python code\server.py
echo [%date% %time%] server exited, restarting in 2 s. Press Ctrl+C to stop.
timeout /t 2 >nul
goto loop
