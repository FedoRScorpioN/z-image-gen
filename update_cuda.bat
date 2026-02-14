@echo off
chcp 65001 >nul 2>&1
title Z-Image-Gen - CUDA Update

echo ================================================
echo   CUDA Runtime DLL Update
echo ================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "BIN_DIR=%INSTALL_DIR%\bin"
set "CUDA_URL=https://github.com/leejet/stable-diffusion.cpp/releases/download/master-504-636d3cb/cudart-sd-bin-win-cu12-x64.zip"
set "CUDA_ZIP=%INSTALL_DIR%\cuda-dlls.zip"

echo Downloading CUDA runtime DLLs...
echo.

python -c "import requests; r=requests.get('%CUDA_URL%', stream=True); f=open(r'%INSTALL_DIR%\cuda-dlls.zip', 'wb'); [f.write(c) for c in r.iter_content(65536)]; f.close(); print('Download complete!')"

if not exist "%CUDA_ZIP%" (
    echo ERROR: Download failed!
    pause
    exit /b 1
)

echo.
echo Extracting...
powershell -Command "Expand-Archive -Path '%CUDA_ZIP%' -DestinationPath '%BIN_DIR%' -Force"

del "%CUDA_ZIP%"

echo.
echo ================================================
echo   Done! CUDA runtime DLLs installed.
echo ================================================
echo.
echo Files in bin folder:
dir /b "%BIN_DIR%\*.dll" 2>nul

echo.
echo Now you can run image generation!
pause
