# PrePol Backend Start Script
# Run this to start the Flask API server

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host "  PrePol API Server - Starting" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("="*59) -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Virtual environment not activated!" -ForegroundColor Yellow
    Write-Host "   Attempting to activate venv..." -ForegroundColor Gray
    
    $venvPath = ".\venv\Scripts\Activate.ps1"
    if (Test-Path $venvPath) {
        & $venvPath
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "❌ Virtual environment not found at $venvPath" -ForegroundColor Red
        Write-Host "   Please create a virtual environment first:" -ForegroundColor Yellow
        Write-Host "   python -m venv venv" -ForegroundColor Gray
        exit 1
    }
}

Write-Host ""
Write-Host "📦 Checking dependencies..." -ForegroundColor Cyan

# Check if Flask is installed
try {
    $flaskVersion = python -c "import flask; print(flask.__version__)" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Flask $flaskVersion installed" -ForegroundColor Green
    } else {
        throw "Flask not installed"
    }
} catch {
    Write-Host "❌ Flask not installed" -ForegroundColor Red
    Write-Host "   Installing dependencies from api/requirements.txt..." -ForegroundColor Yellow
    pip install -r api/requirements.txt
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Dependencies installed" -ForegroundColor Green
}

Write-Host ""
Write-Host "🔍 Checking model and data files..." -ForegroundColor Cyan

# Check model files
$modelFiles = Get-ChildItem -Path "model" -Filter "rf_crime_model_*.joblib" -ErrorAction SilentlyContinue
if ($modelFiles.Count -eq 0) {
    Write-Host "❌ Model files not found in model/" -ForegroundColor Red
    Write-Host "   Please run ModelTraining.ipynb first to generate the model" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Model found: $($modelFiles[0].Name)" -ForegroundColor Green
}

# Check panel data
$panelPath = "notebooks\prepol_out\PrePol_panel_export.parquet"
if (-not (Test-Path $panelPath)) {
    Write-Host "❌ Panel data not found at $panelPath" -ForegroundColor Red
    Write-Host "   Please run H3Discretization.ipynb first to generate panel data" -ForegroundColor Yellow
    exit 1
} else {
    $panelSize = (Get-Item $panelPath).Length / 1MB
    Write-Host "✓ Panel data found: $([math]::Round($panelSize, 1)) MB" -ForegroundColor Green
}

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("="*59) -ForegroundColor Green
Write-Host "  Starting Flask API Server" -ForegroundColor White
Write-Host "=" -NoNewline -ForegroundColor Green
Write-Host ("="*59) -ForegroundColor Green
Write-Host ""

# Start the server
python api/server.py
