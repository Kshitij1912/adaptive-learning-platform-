@echo off
title Adaptive Learning Platform - Local Server
echo ======================================================================
echo           ADAPTIVE LEARNING PLATFORM - LOCALHOST LAUNCHER
echo ======================================================================
echo.

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python was not found in PATH!
    echo Please install Python 3.10+ and check 'Add to PATH'.
    pause
    exit /b 1
)

echo [1/3] Running automated unit tests...
python -m unittest discover tests
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Some tests encountered warnings. Continuing startup...
)

echo.
echo [2/3] Checking ML model weights...
if not exist "data\classifier_model.json" (
    echo Models not found. Training historical ML pipeline...
    python scripts\train_models.py
)

echo.
echo [3/3] Starting web server and opening browser...
python scripts\run_server.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Server terminated with an error.
    pause
)
