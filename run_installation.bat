@echo off
title Maveli AI - Installation Orchestrator & Projector
echo ========================================================
echo   👑 MAVELI AI (PĀTĀḶA KĀVAL) - INSTALLATION LAUNCHER
echo ========================================================
echo.
echo 1. Starting FastAPI & WebSocket Display Server on port 8000...
echo 2. Opening Projector Display in your default browser...
echo.

start http://localhost:8000/

.\venv\Scripts\python.exe main.py
pause
