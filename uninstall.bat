@echo off
echo =====================================================
echo          Z-Image Generator - Uninstall
echo =====================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"

if not exist "%INSTALL_DIR%" (
    echo Not installed.
    pause
    exit /b 0
)

echo Will delete: %INSTALL_DIR%
echo (~6 GB of data)
echo.
choice /C YN /M "Are you sure"
if %errorLevel% equ 2 exit /b 0

rmdir /s /q "%INSTALL_DIR%" 2>nul
del "%USERPROFILE%\Desktop\Z-Image-Gen.lnk" 2>nul

echo Done!
pause
