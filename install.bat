@echo off
echo =====================================================
echo         Z-Image Generator - Installer
echo =====================================================
echo.

set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "VENV_DIR=%INSTALL_DIR%\venv"

echo Step 1: Checking Python...
python --version
if %errorLevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK!
echo.

echo Step 2: Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
echo OK!
echo.

echo Step 3: Creating virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
)
echo OK!
echo.

echo Step 4: Installing Python packages...
call "%VENV_DIR%\Scripts\activate.bat"
python -m pip install --upgrade pip --quiet
pip install requests --quiet
echo OK!
echo.

echo Step 5: Copying generate.py...
copy /Y "%~dp0generate.py" "%INSTALL_DIR%\generate.py" >nul
echo OK!
echo.

echo Step 6: Downloading sd-cli and models...
echo This will download ~5 GB of data.
echo.
python "%INSTALL_DIR%\generate.py" --install
echo.

echo Step 7: Creating launcher...

:: Create run.bat
(
echo @echo off
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python "%INSTALL_DIR%\generate.py" %%*
echo if "%%1"=="" pause
) > "%INSTALL_DIR%\run.bat"

:: Desktop shortcut
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Z-Image-Gen.lnk'); $s.TargetPath = '%INSTALL_DIR%\run.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Save()"

echo OK!
echo.

echo =====================================================
echo              INSTALLATION COMPLETE!
echo =====================================================
echo.
echo Usage:
echo   %INSTALL_DIR%\run.bat "your prompt"
echo.
echo Example:
echo   %INSTALL_DIR%\run.bat "beautiful sunset"
echo.
echo Or use desktop shortcut: Z-Image-Gen
echo =====================================================
pause
