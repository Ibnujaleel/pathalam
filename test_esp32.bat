@echo off
title ESP32 Live Telemetry Tester
echo ========================================================
echo   SCANNING & TESTING ESP32 SERIAL INTERFACE
echo ========================================================
echo.
echo NOTE: Please make sure Arduino IDE Serial Monitor is CLOSED!
echo.
.\venv\Scripts\python.exe test_esp32_connection.py
pause
