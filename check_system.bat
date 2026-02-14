@echo off
chcp 65001 >nul
title System Check - Z-Image Generator

echo.
echo ═══════════════════════════════════════════════════════════════
echo               Z-Image Generator - System Check
echo ═══════════════════════════════════════════════════════════════
echo.

:: Check OS
echo [OS Information]
ver
echo.

:: Check Python
echo [Python]
python --version 2>nul
if %errorLevel% neq 0 (
    echo Status: NOT INSTALLED
    echo Download: https://www.python.org/downloads/
) else (
    echo Status: OK
)
echo.

:: Check NVIDIA GPU
echo [NVIDIA GPU]
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>nul
if %errorLevel% neq 0 (
    echo Status: NOT DETECTED
    echo Required: NVIDIA GPU with CUDA support
    echo Drivers: https://www.nvidia.com/Download/index.aspx
) else (
    echo Status: OK
)
echo.

:: Check CUDA
echo [CUDA]
nvcc --version 2>nul | findstr "release"
if %errorLevel% neq 0 (
    echo Status: NOT FOUND
    echo Note: CUDA will be used via PyTorch if available
) else (
    echo Status: OK
)
echo.

:: Check available disk space
echo [Disk Space]
for /f "tokens=3" %%a in ('dir /-C %LOCALAPPDATA% 2^>nul ^| findstr /C:"bytes free"') do set FREE=%%a
echo Free space on system drive: %FREE% bytes
echo Required: ~5 GB for installation
echo.

:: Check RAM
echo [System Memory]
wmic OS get TotalVisibleMemorySize /value 2>nul | findstr "="
echo.

echo ═══════════════════════════════════════════════════════════════
echo                    System check complete
echo ═══════════════════════════════════════════════════════════════
echo.
pause
