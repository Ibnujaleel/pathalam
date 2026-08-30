@echo off
title Retraining ML Classifier (12-bit ADC)
echo ========================================================
echo   TRAINING RANDOM FOREST ACTION CLASSIFIER (12-bit ADC)
echo ========================================================
echo.
.\venv\Scripts\python.exe ml_pipeline.py
echo.
echo Model training complete.
pause
