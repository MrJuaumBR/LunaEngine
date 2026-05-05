@echo off
title LunaEngine Build & Deploy Script
setlocal enabledelayedexpansion

echo ===================================================
echo   LunaEngine - Full Build & Deploy Pipeline
echo ===================================================
echo.

:: ---------------------------------------------------
:: 0. Check prerequisites
:: ---------------------------------------------------
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
)

where twine >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Twine not found. Install with: pip install twine
    pause
    exit /b 1
)

:: ---------------------------------------------------
:: 1. Optional Git commit
:: ---------------------------------------------------
echo [1/7] Git commit (optional)
set /p commit_choice="Do you want to commit current changes to GitHub? (y/N): "
if /i "!commit_choice!"=="y" (
    set /p commit_msg="Enter commit message: "
    if "!commit_msg!"=="" set commit_msg="Automated build script commit"
    git add .
    git commit -m "!commit_msg!"
    if %errorlevel% neq 0 (
        echo [WARNING] Git commit failed. Continuing anyway...
    ) else (
        echo [INFO] Committed successfully. Now pushing...
        git push
        if %errorlevel% neq 0 (
            echo [WARNING] Git push failed. Continue manually later.
        )
    )
) else (
    echo Skipping Git commit.
)
echo.

:: ---------------------------------------------------
:: 2. Build documentation
:: ---------------------------------------------------
echo [2/7] Building documentation...
if not exist "build_docs.bat" (
    echo [ERROR] build_docs.bat not found in current directory.
    pause
    exit /b 1
)
call build_docs.bat
if %errorlevel% neq 0 (
    echo [ERROR] Documentation build failed.
    pause
    exit /b %errorlevel%
)
echo.

:: ---------------------------------------------------
:: 3. Clean old dist folder
:: ---------------------------------------------------
echo [3/7] Cleaning old dist folder...
if exist "dist" (
    rmdir /s /q dist
    echo Removed existing dist folder.
)
echo.

:: ---------------------------------------------------
:: 4. Build distribution
:: ---------------------------------------------------
echo [4/7] Building distribution (python -m build)...
python -m build
if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b %errorlevel%
)
echo.

:: ---------------------------------------------------
:: 5. Check distribution files
:: ---------------------------------------------------
echo [5/7] Checking distribution with twine...
twine check dist/*
if %errorlevel% neq 0 (
    echo [ERROR] twine check failed.
    pause
    exit /b %errorlevel%
)
echo.

:: ---------------------------------------------------
:: 6. Upload to TestPyPI
:: ---------------------------------------------------
echo [6/7] Upload to TestPyPI
set /p test_choice="Upload to TestPyPI? (y/N): "
if /i "!test_choice!"=="y" (
    twine upload --config-file .pypirc --repository testpypi dist/*
    if %errorlevel% neq 0 (
        echo [ERROR] TestPyPI upload failed.
        pause
        exit /b %errorlevel%
    )
    echo [SUCCESS] Uploaded to TestPyPI.
) else (
    echo Skipping TestPyPI upload.
)
echo.

:: ---------------------------------------------------
:: 7. Upload to PyPI (production)
:: ---------------------------------------------------
echo [7/7] Upload to PyPI
set /p pypi_choice="Upload to PyPI (production)? (y/N): "
if /i "!pypi_choice!"=="y" (
    twine upload --config-file .pypirc --repository pypi dist/*
    if %errorlevel% neq 0 (
        echo [ERROR] PyPI upload failed.
        pause
        exit /b %errorlevel%
    )
    echo [SUCCESS] Uploaded to PyPI.
) else (
    echo Skipping PyPI upload.
)

echo.
echo ===================================================
echo   All selected steps completed successfully!
echo ===================================================
pause