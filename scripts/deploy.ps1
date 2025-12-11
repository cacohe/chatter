# 设置控制台编码为 UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Production Deployment Script (PowerShell)
# For Windows systems
# 
# Usage:
#   .\scripts\deploy.ps1
#   or
#   powershell -ExecutionPolicy Bypass -File .\scripts\deploy.ps1
# 
# Note: This script must be run in PowerShell, not with sh or bash

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Multi-Model AI Chatbot - Deployment Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check Docker and Docker Compose
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker not installed, please install Docker Desktop" -ForegroundColor Red
    exit 1
}

if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Docker Compose not installed, please install Docker Compose" -ForegroundColor Red
    exit 1
}

# Check if Docker daemon is running
Write-Host "Checking Docker daemon..." -ForegroundColor Yellow
$dockerCheck = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Error: Docker daemon is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please do the following:" -ForegroundColor Yellow
    Write-Host "  1. Start Docker Desktop" -ForegroundColor Yellow
    Write-Host "  2. Wait for Docker Desktop to fully start (check system tray)" -ForegroundColor Yellow
    Write-Host "  3. Verify Docker is running: docker version" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $dockerCheck -ForegroundColor Red
    exit 1
}
Write-Host "Docker daemon is running" -ForegroundColor Green

# Switch to project root directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# Check .env file
if (-not (Test-Path .env)) {
    Write-Host "Warning: .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    if (Test-Path .env.example) {
        Copy-Item .env.example .env
        Write-Host "Please edit .env file and fill in necessary configuration" -ForegroundColor Yellow
        Read-Host "Press Enter to continue..."
    } else {
        Write-Host "Error: .env.example file not found" -ForegroundColor Red
        exit 1
    }
}

# Select operation
Write-Host ""
Write-Host "Please select an operation:" -ForegroundColor Green
Write-Host "1) Build and start services"
Write-Host "2) Start services only (no rebuild)"
Write-Host "3) Stop services"
Write-Host "4) Restart services"
Write-Host "5) View logs"
Write-Host "6) Clean and redeploy"
$choice = Read-Host "Enter option (1-6)"

switch ($choice) {
    "1" {
        Write-Host "Building and starting services..." -ForegroundColor Green
        Set-Location docker
        $buildResult = docker-compose build 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Build failed!" -ForegroundColor Red
            Write-Host $buildResult -ForegroundColor Red
            Set-Location ..
            exit 1
        }
        $upResult = docker-compose up -d 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Start failed!" -ForegroundColor Red
            Write-Host $upResult -ForegroundColor Red
            Set-Location ..
            exit 1
        }
        Set-Location ..
        Write-Host "Services started!" -ForegroundColor Green
        Write-Host "Backend API: http://localhost:8000"
        Write-Host "Frontend UI: http://localhost:8501"
        Write-Host "API Docs: http://localhost:8000/docs"
    }
    "2" {
        Write-Host "Starting services..." -ForegroundColor Green
        Set-Location docker
        $upResult = docker-compose up -d 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Start failed!" -ForegroundColor Red
            Write-Host $upResult -ForegroundColor Red
            Write-Host ""
            Write-Host "Possible causes:" -ForegroundColor Yellow
            Write-Host "  1. Docker daemon is not running" -ForegroundColor Yellow
            Write-Host "  2. Services are already running" -ForegroundColor Yellow
            Write-Host "  3. Port conflicts" -ForegroundColor Yellow
            Set-Location ..
            exit 1
        }
        Set-Location ..
        Write-Host "Services started!" -ForegroundColor Green
    }
    "3" {
        Write-Host "Stopping services..." -ForegroundColor Yellow
        Set-Location docker
        docker-compose down 2>&1 | Out-Null
        Set-Location ..
        Write-Host "Services stopped" -ForegroundColor Yellow
    }
    "4" {
        Write-Host "Restarting services..." -ForegroundColor Green
        Set-Location docker
        $restartResult = docker-compose restart 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Restart failed!" -ForegroundColor Red
            Write-Host $restartResult -ForegroundColor Red
            Set-Location ..
            exit 1
        }
        Set-Location ..
        Write-Host "Services restarted" -ForegroundColor Green
    }
    "5" {
        Write-Host "Viewing logs (Press Ctrl+C to exit)..." -ForegroundColor Green
        Set-Location docker
        docker-compose logs -f
        Set-Location ..
    }
    "6" {
        Write-Host "Cleaning and redeploying..." -ForegroundColor Yellow
        Set-Location docker
        docker-compose down -v 2>&1 | Out-Null
        $buildResult = docker-compose build --no-cache 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Build failed!" -ForegroundColor Red
            Write-Host $buildResult -ForegroundColor Red
            Set-Location ..
            exit 1
        }
        $upResult = docker-compose up -d 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Start failed!" -ForegroundColor Red
            Write-Host $upResult -ForegroundColor Red
            Set-Location ..
            exit 1
        }
        Set-Location ..
        Write-Host "Services redeployed!" -ForegroundColor Green
    }
    default {
        Write-Host "Invalid option" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
