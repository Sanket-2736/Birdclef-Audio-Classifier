# System Verification Script - BirdCLEF Audio Classifier
# Run this to verify all components are installed and ready

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BirdCLEF Audio Classifier - System Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0
$warnings = 0

# ===== BACKEND CHECKS =====
Write-Host "BACKEND VERIFICATION" -ForegroundColor Yellow
Write-Host "--------------------"

# Check Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion"
} catch {
    Write-Host "❌ Python not found" -ForegroundColor Red
    $errors++
}

# Check backend directory
if (Test-Path "backend") {
    Write-Host "✅ Backend directory exists"
} else {
    Write-Host "❌ Backend directory missing" -ForegroundColor Red
    $errors++
}

# Check key backend files
$backendFiles = @(
    "backend\app\main.py",
    "backend\app\storage.py",
    "backend\app\pipeline.py",
    "backend\app\config.py",
    "backend\app\routers\recordings.py"
)

foreach ($file in $backendFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists"
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        $errors++
    }
}

# Check Python dependencies
Write-Host ""
Write-Host "Checking Python dependencies..."
try {
    python -c "import fastapi, sqlalchemy, soundfile, numpy, onnxruntime" 2>&1 | Out-Null
    Write-Host "✅ All Python dependencies installed"
} catch {
    Write-Host "⚠️  Some Python dependencies may be missing" -ForegroundColor Yellow
    $warnings++
}

# Check database
Write-Host ""
if (Test-Path "backend\birdclef.db") {
    Write-Host "✅ Database file exists"
} else {
    Write-Host "ℹ️  Database file will be created on first run" -ForegroundColor Cyan
    $warnings++
}

# ===== FRONTEND CHECKS =====
Write-Host ""
Write-Host "FRONTEND VERIFICATION" -ForegroundColor Yellow
Write-Host "---------------------"

# Check frontend directory
if (Test-Path "frontend") {
    Write-Host "✅ Frontend directory exists"
} else {
    Write-Host "❌ Frontend directory missing" -ForegroundColor Red
    $errors++
}

# Check Node.js
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✅ Node.js: $nodeVersion"
} catch {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
    $errors++
}

# Check npm
try {
    $npmVersion = npm --version 2>&1
    Write-Host "✅ npm: $npmVersion"
} catch {
    Write-Host "❌ npm not found" -ForegroundColor Red
    $errors++
}

# Check key frontend files
$frontendFiles = @(
    "frontend\src\App.jsx",
    "frontend\src\pages\Analyze.jsx",
    "frontend\src\pages\Results.jsx",
    "frontend\src\components\ProgressStepper.jsx",
    "frontend\src\hooks\useRecordingUpload.js",
    "frontend\package.json"
)

foreach ($file in $frontendFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file exists"
    } else {
        Write-Host "❌ $file missing" -ForegroundColor Red
        $errors++
    }
}

# Check node_modules
Write-Host ""
if (Test-Path "frontend\node_modules") {
    Write-Host "✅ Node modules installed"
} else {
    Write-Host "ℹ️  Node modules not installed (run 'npm install' in frontend/)" -ForegroundColor Cyan
    $warnings++
}

# ===== PYTHON SYNTAX CHECK =====
Write-Host ""
Write-Host "PYTHON SYNTAX VERIFICATION" -ForegroundColor Yellow
Write-Host "---------------------------"

$pythonFiles = @(
    "backend\app\storage.py",
    "backend\app\routers\recordings.py",
    "backend\app\pipeline.py"
)

foreach ($file in $pythonFiles) {
    try {
        python -m py_compile $file 2>&1 | Out-Null
        Write-Host "✅ $file - syntax OK"
    } catch {
        Write-Host "❌ $file - syntax error" -ForegroundColor Red
        $errors++
    }
}

# ===== STORAGE DIRECTORY =====
Write-Host ""
Write-Host "STORAGE VERIFICATION" -ForegroundColor Yellow
Write-Host "--------------------"

if (Test-Path "storage\audio") {
    Write-Host "✅ Storage directory exists"
} else {
    Write-Host "ℹ️  Storage directory will be created on first upload" -ForegroundColor Cyan
}

# ===== SUMMARY =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "VERIFICATION SUMMARY" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    Write-Host "✅ SYSTEM READY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Terminal 1: cd backend ; uvicorn app.main:app --reload" 
    Write-Host "2. Terminal 2: cd frontend ; npm run dev"
    Write-Host "3. Browser: http://localhost:5173/register"
    Write-Host ""
} else {
    Write-Host "Errors: $errors" -ForegroundColor Red
    if ($warnings -gt 0) {
        Write-Host "Warnings: $warnings" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "❌ Please fix errors before starting" -ForegroundColor Red
}
