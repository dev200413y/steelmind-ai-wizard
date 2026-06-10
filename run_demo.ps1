# SteelMind AI Wizard - Startup Script
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    Starting SteelMind AI Wizard" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if data generation is needed
$SensorCsv = "src\data\sensor_data.csv"
$IsoForest = "src\models\isolation_forest.pkl"
$FaissIndex = "src\knowledge_base\faiss_index\index.faiss"

if (!(Test-Path $IsoForest) -or !(Test-Path $FaissIndex)) {
    Write-Host "Running initial setup (Data Generation & Model Training)..." -ForegroundColor Yellow
    $env:PYTHONIOENCODING="utf8"
    python src\data\generate_sensor_data.py
    python src\data\generate_maintenance_logs.py
    python src\data\generate_knowledge_docs.py
    python src\models\train_models.py
    python src\knowledge_base\index_docs.py
}

# Start FastAPI Backend in background
Write-Host "Starting FastAPI Backend on port 8000..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath "uvicorn" -ArgumentList "main:app --host 0.0.0.0 --port 8000"

# Start React Frontend
Write-Host "Starting React Frontend on port 5173..." -ForegroundColor Green
Set-Location frontend
npm run dev
