@echo off
chcp 65001 >nul 2>&1
set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "VENV_DIR=%INSTALL_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ERROR: Not installed. Run install.bat first.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"

:: If arguments provided, run single command mode
if not "%~1"=="" (
    python "%INSTALL_DIR%\generate.py" %*
) else (
    :: Otherwise run interactive mode
    python "%INSTALL_DIR%\generate.py" --interactive
)
