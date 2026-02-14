@echo off
set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "VENV_DIR=%INSTALL_DIR%\venv"

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo ERROR: Not installed. Run install.bat first.
    pause
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
python "%INSTALL_DIR%\generate.py" %*

if "%1"=="" pause
