@echo off
title LunaEngine Documentation Builder

echo =====================================
echo   LunaEngine Documentation Builder
echo =====================================

REM 1. Clear Python cache files
echo.
echo [1/3] Cleaning __pycache__ directories...
python lunaengine\tools\clear_pycache.py
if errorlevel 1 (
    echo ERROR: clear_pycache.py failed
    pause
    exit /b %errorlevel%
)

REM 2. Generate code statistics
echo.
echo [2/3] Generating code statistics...
python lunaengine\tools\code_stats.py
if errorlevel 1 (
    echo ERROR: code_stats.py failed
    pause
    exit /b %errorlevel%
)

REM 3. Build the full documentation website
echo.
echo [3/3] Building HTML documentation...
python generate_docs.py
if errorlevel 1 (
    echo ERROR: generate_docs.py failed
    pause
    exit /b %errorlevel%
)

echo.
echo =====================================
echo   Documentation build completed!
echo   Output folder: docs/
echo =====================================
pause