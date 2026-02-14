@echo off
chcp 65001 >nul 2>&1
title System Check - Z-Image Generator

echo.
echo ===============================================================
echo              Z-Image Generator - System Check
echo ===============================================================
echo.

:: Check OS
echo [Operating System]
ver
echo.

:: Check Python
echo [Python]
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo Status: NOT INSTALLED
    echo Download: https://www.python.org/downloads/
    echo Note: Make sure to check "Add Python to PATH" during installation
) else (
    python --version
    echo Status: OK
)
echo.

:: Check pip
echo [pip]
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo Status: NOT AVAILABLE
) else (
    python -m pip --version
    echo Status: OK
)
echo.

:: Check NVIDIA GPU
echo [NVIDIA GPU]
where nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    if exist "C:\Windows\System32\nvidia-smi.exe" (
        "C:\Windows\System32\nvidia-smi.exe" --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>nul
        if %errorLevel% equ 0 (
            echo Status: OK
            goto :gpu_done
        )
    )
    if exist "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" (
        "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>nul
        if %errorLevel% equ 0 (
            echo Status: OK
            goto :gpu_done
        )
    )
    echo Status: NOT DETECTED
    echo Required: NVIDIA GPU with CUDA support
    echo Drivers: https://www.nvidia.com/Download/index.aspx
) else (
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    echo Status: OK
)
:gpu_done
echo.

:: Check CUDA via PyTorch
echo [CUDA via PyTorch]
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')" 2>nul
if %errorLevel% neq 0 (
    echo Status: PyTorch not installed or CUDA not available
    echo Note: Will be installed during setup
) else (
    echo Status: OK
)
echo.

:: Check disk space
echo [Disk Space]
for /f "skip=1 tokens=3" %%a in ('dir /-C %LOCALAPPDATA% 2^>nul') do set FREE_SPACE=%%a
echo Available on system drive: %FREE_SPACE% bytes
echo Required: ~5 GB for installation
echo.

:: Check RAM
echo [System Memory]
systeminfo | findstr /C:"Total Physical Memory" 2>nul
echo.

echo ===============================================================
echo                   System check complete
echo ===============================================================
echo.
echo If all checks passed, run install.bat to continue.
echo.
pause
