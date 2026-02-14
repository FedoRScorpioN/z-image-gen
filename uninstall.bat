@echo off
chcp 65001 >nul 2>&1
title Uninstall Z-Image Generator

echo.
echo ===============================================================
echo              Z-Image Generator - Uninstall
echo ===============================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"

if not exist "%INSTALL_DIR%" (
    echo Z-Image Generator is not installed.
    echo.
    pause
    exit /b 0
)

echo This will remove:
echo   - Virtual environment
echo   - Downloaded models (~4 GB)
echo   - Configuration files
echo.
echo Location: %INSTALL_DIR%
echo.

set /p CONFIRM="Continue? (y/N): "
if /i not "%CONFIRM%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Removing installation...

:: Remove installation directory
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%" 2>nul
    echo [OK] Removed: %INSTALL_DIR%
)

:: Remove desktop shortcut
set "SHORTCUT=%USERPROFILE%\Desktop\Z-Image-Gen.lnk"
if exist "%SHORTCUT%" (
    del "%SHORTCUT%" 2>nul
    echo [OK] Removed: Desktop shortcut
)

echo.
echo ===============================================================
echo                    Uninstall complete!
echo ===============================================================
echo.
pause
