@echo off
echo =====================================================
echo          Z-Image Generator - System Check
echo =====================================================
echo.

echo [Operating System]
ver
echo.

echo [Python]
python --version 2>nul
if %errorLevel% neq 0 (
    echo NOT INSTALLED
    echo Download: https://www.python.org/downloads/
) else (
    echo OK
)
echo.

echo [pip]
pip --version 2>nul
if %errorLevel% neq 0 (
    echo NOT AVAILABLE
) else (
    echo OK
)
echo.

echo [NVIDIA GPU]
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader 2>nul
if %errorLevel% neq 0 (
    echo NOT DETECTED
    echo Required: NVIDIA GPU with CUDA support
    echo Drivers: https://www.nvidia.com/Download/index.aspx
) else (
    echo OK
)
echo.

echo [Disk Space]
wmic logicaldisk get size,freespace,caption 2>nul
echo Required: ~5 GB
echo.

echo =====================================================
echo If all checks show OK, run install.bat
echo =====================================================
pause
