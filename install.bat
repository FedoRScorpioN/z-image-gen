@echo off
chcp 65001 >nul 2>&1
title Z-Image Generator - Installer

echo.
echo ===============================================================
echo            Z-Image Generator - Auto Installer
echo            Optimized for 4GB VRAM
echo ===============================================================
echo.

:: Set installation directory
set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "MODEL_DIR=%INSTALL_DIR%\models"
set "VENV_DIR=%INSTALL_DIR%\venv"

echo [INFO] Installation directory: %INSTALL_DIR%
echo.

:: Step 1: Check Python
echo [1/6] Checking Python installation...
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found!
    echo.
    echo Please install Python 3.10+ from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    goto :error
)
echo [OK] Python found:
python --version
echo.

:: Step 2: Check pip
echo [2/6] Checking pip...
python -m pip --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] pip not found!
    echo Please reinstall Python with pip included.
    goto :error
)
echo [OK] pip available
echo.

:: Step 3: Check NVIDIA GPU
echo [3/6] Checking NVIDIA GPU...
where nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] nvidia-smi not found in PATH
    echo [INFO] Trying common locations...
    
    if exist "C:\Windows\System32\nvidia-smi.exe" (
        "C:\Windows\System32\nvidia-smi.exe" --query-gpu=name --format=csv,noheader 2>nul
        if %errorLevel% equ 0 (
            echo [OK] NVIDIA GPU detected
            goto :gpu_ok
        )
    )
    
    if exist "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" (
        "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe" --query-gpu=name --format=csv,noheader 2>nul
        if %errorLevel% equ 0 (
            echo [OK] NVIDIA GPU detected
            goto :gpu_ok
        )
    )
    
    echo [WARNING] NVIDIA GPU not detected automatically
    echo [INFO] If you have NVIDIA GPU, you can continue anyway
    echo.
    set /p CONTINUE="Continue anyway? (y/n): "
    if /i not "%CONTINUE%"=="y" goto :error
)
:gpu_ok
echo.

:: Step 4: Create directories
echo [4/6] Creating installation directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
echo [OK] Directories created
echo.

:: Step 5: Create virtual environment
echo [5/6] Setting up Python virtual environment...
if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
    if %errorLevel% neq 0 (
        echo [ERROR] Failed to create virtual environment!
        goto :error
    )
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)
echo.

:: Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

:: Upgrade pip
echo [INFO] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Step 6: Install dependencies
echo [6/6] Installing dependencies...
echo [INFO] This may take 5-10 minutes on first run...
echo.

echo [INFO] Installing PyTorch with CUDA support...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet --disable-pip-version-check
if %errorLevel% neq 0 (
    echo [WARNING] PyTorch installation had issues, continuing...
)

echo [INFO] Installing stable-diffusion-cpp-python...
set CMAKE_ARGS=-DSD_CUDA=ON
pip install cmake --quiet --disable-pip-version-check
pip install stable-diffusion-cpp-python --quiet --disable-pip-version-check
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install stable-diffusion-cpp-python!
    echo [INFO] Try running: pip install stable-diffusion-cpp-python
    goto :error
)

echo [INFO] Installing other dependencies...
pip install requests pillow tqdm huggingface-hub --quiet --disable-pip-version-check

echo [OK] Dependencies installed
echo.

:: Download model
echo ===============================================================
echo Downloading Z-Image-Turbo Model (Q4_0 - 3.68 GB)
echo ===============================================================
echo.

set "MODEL_PATH=%MODEL_DIR%\z_image_turbo-Q4_0.gguf"
set "MODEL_URL=https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf"

if exist "%MODEL_PATH%" (
    for %%A in ("%MODEL_PATH%") do set MODEL_SIZE=%%~zA
    if %MODEL_SIZE% GTR 3000000000 (
        echo [OK] Model already downloaded
        goto :model_done
    )
)

echo [INFO] Downloading model... This may take 10-30 minutes.
echo [INFO] Please wait, do not close this window!
echo.

:: Use PowerShell for download with progress
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$url = '%MODEL_URL%'; $output = '%MODEL_PATH%'; $ProgressPreference = 'SilentlyContinue'; Write-Host 'Starting download...'; try { Invoke-WebRequest -Uri $url -OutFile $output -UseBasicParsing; Write-Host 'Download complete!' } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 }"

if not exist "%MODEL_PATH%" (
    echo [ERROR] Model download failed!
    echo.
    echo Please download manually from:
    echo %MODEL_URL%
    echo And save to: %MODEL_PATH%
    goto :error
)

:model_done
echo [OK] Model ready
echo.

:: Create launcher script
echo [INFO] Creating launcher scripts...

:: Create run.bat in install dir
(
echo @echo off
echo chcp 65001 ^>nul 2^>^&1
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python "%INSTALL_DIR%\generate.py" %%*
echo if "%%1"=="" (
echo     echo.
echo     echo Usage: run.bat "your prompt here"
echo     echo Example: run.bat "beautiful sunset"
echo     pause
echo ^)
) > "%INSTALL_DIR%\run.bat"

:: Copy generate.py
copy /Y "%~dp0generate.py" "%INSTALL_DIR%\generate.py" >nul

echo [OK] Scripts created
echo.

:: Create desktop shortcut using PowerShell
echo [INFO] Creating desktop shortcut...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Z-Image-Gen.lnk'); $s.TargetPath = '%INSTALL_DIR%\run.bat'; $s.WorkingDirectory = '%INSTALL_DIR%'; $s.Description = 'Z-Image Generator'; $s.Save(); Write-Host 'Desktop shortcut created'"

echo.
echo ===============================================================
echo                  INSTALLATION COMPLETE!
echo ===============================================================
echo.
echo   Installation directory: %INSTALL_DIR%
echo   Model location: %MODEL_PATH%
echo.
echo   USAGE:
echo   ---------------------------------------------------------------
echo   Open Command Prompt and run:
echo   "%INSTALL_DIR%\run.bat" "your prompt here"
echo.
echo   Example:
echo   "%INSTALL_DIR%\run.bat" "beautiful sunset over mountains"
echo.
echo   Or use the desktop shortcut: Z-Image-Gen
echo.
echo   Images will be saved to your Downloads folder.
echo ===============================================================
echo.
echo Press any key to run a test generation...
pause >nul

:: Test run
echo.
echo [INFO] Running test generation...
echo [INFO] This may take a minute on first run...
echo.
call "%INSTALL_DIR%\run.bat" "a cute cat sitting on a windowsill"

echo.
echo ===============================================================
echo Test complete! Check your Downloads folder for the image.
echo ===============================================================
pause
exit /b 0

:error
echo.
echo ===============================================================
echo                    INSTALLATION FAILED
echo ===============================================================
echo.
echo Please check the errors above and try again.
echo.
pause
exit /b 1
