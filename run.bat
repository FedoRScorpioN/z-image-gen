@echo off
chcp 65001 >nul
title Z-Image Generator

:: Check if installed
if not exist "%LOCALAPPDATA%\z-image-gen\venv\Scripts\activate.bat" (
    echo [!] Z-Image Generator is not installed!
    echo [*] Please run install.bat first.
    pause
    exit /b 1
)

:: Activate environment and run
call "%LOCALAPPDATA%\z-image-gen\venv\Scripts\activate.bat"
python "%LOCALAPPDATA%\z-image-gen\generate.py" %*
