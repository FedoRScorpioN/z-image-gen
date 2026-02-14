@echo off
chcp 65001 >nul 2>&1
title Z-Image Generator

set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "VENV_DIR=%INSTALL_DIR%\venv"
set "GENERATE_PY=%INSTALL_DIR%\generate.py"

:: Check if installed
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo.
    echo [ERROR] Z-Image Generator is not installed!
    echo.
    echo Please run install.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "%GENERATE_PY%" (
    echo.
    echo [ERROR] generate.py not found!
    echo.
    echo Please reinstall by running install.bat
    echo.
    pause
    exit /b 1
)

:: Activate environment and run
call "%VENV_DIR%\Scripts\activate.bat"
python "%GENERATE_PY%" %*

:: If no arguments, show help and pause
if "%1"=="" (
    echo.
    pause
)
