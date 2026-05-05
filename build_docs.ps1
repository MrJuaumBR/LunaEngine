# build_docs.ps1
# Runs the documentation generation pipeline for LunaEngine

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  LunaEngine Documentation Builder" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Get the directory where this script resides (project root)
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

# 1. Clear Python cache files
Write-Host "`n[1/3] Cleaning __pycache__ directories..." -ForegroundColor Yellow
python lunaengine/tools/clear_pycache.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: clear_pycache.py failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 2. Generate code statistics
Write-Host "`n[2/3] Generating code statistics..." -ForegroundColor Yellow
python lunaengine/tools/code_stats.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: code_stats.py failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

# 3. Build the full documentation website
Write-Host "`n[3/3] Building HTML documentation..." -ForegroundColor Yellow
python generate_docs.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: generate_docs.py failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "`n=====================================" -ForegroundColor Green
Write-Host "  Documentation build completed!" -ForegroundColor Green
Write-Host "  Output folder: docs/" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green