@echo off
echo =====================================================
echo         Z-Image Generator - Installer
echo =====================================================
echo.

:: Set paths
set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "MODEL_DIR=%INSTALL_DIR%\models"
set "VENV_DIR=%INSTALL_DIR%\venv"

echo Step 1: Checking Python...
python --version
if %errorLevel% neq 0 (
    echo.
    echo ERROR: Python not found!
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH"
    pause
    exit /b 1
)
echo OK!
echo.

echo Step 2: Checking NVIDIA GPU...
nvidia-smi --query-gpu=name --format=csv,noheader 2>nul
if %errorLevel% neq 0 (
    echo WARNING: NVIDIA GPU not detected.
    echo If you have NVIDIA GPU, install drivers from:
    echo https://www.nvidia.com/Download/index.aspx
    echo.
    choice /C YN /M "Continue anyway"
    if %errorLevel% equ 2 exit /b 1
)
echo OK!
echo.

echo Step 3: Creating directories...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
echo OK!
echo.

echo Step 4: Creating virtual environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    if %errorLevel% neq 0 (
        echo ERROR: Failed to create venv
        pause
        exit /b 1
    )
)
echo OK!
echo.

echo Step 5: Installing dependencies...
echo This will take a few minutes...
echo.

call "%VENV_DIR%\Scripts\activate.bat"

echo Installing pip...
python -m pip install --upgrade pip --quiet

echo Installing PyTorch...
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet

echo Installing stable-diffusion-cpp-python...
set CMAKE_ARGS=-DSD_CUDA=ON
pip install cmake --quiet
pip install stable-diffusion-cpp-python --quiet
if %errorLevel% neq 0 (
    echo ERROR: Failed to install stable-diffusion-cpp-python
    pause
    exit /b 1
)

echo Installing other packages...
pip install requests pillow tqdm --quiet

echo OK!
echo.

echo Step 6: Downloading model (3.7 GB)...
set "MODEL_PATH=%MODEL_DIR%\z_image_turbo-Q4_0.gguf"

if exist "%MODEL_PATH%" (
    echo Model already exists, skipping download.
    goto :skip_download
)

echo Downloading... This will take 10-30 minutes.
echo Do NOT close this window!
echo.

powershell -Command "Invoke-WebRequest -Uri 'https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf' -OutFile '%MODEL_PATH%' -UseBasicParsing"

if not exist "%MODEL_PATH%" (
    echo ERROR: Download failed
    pause
    exit /b 1
)

:skip_download
echo OK!
echo.

echo Step 7: Creating launcher...

:: Copy generate.py
copy /Y "%~dp0generate.py" "%INSTALL_DIR%\generate.py" >nul

:: Create run.bat
(
echo @echo off
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python "%INSTALL_DIR%\generate.py" %%*
echo if "%%1"=="" pause
) > "%INSTALL_DIR%\run.bat"

echo OK!
echo.

echo =====================================================
echo              INSTALLATION COMPLETE!
echo =====================================================
echo.
echo To generate images, run:
echo   %INSTALL_DIR%\run.bat "your prompt here"
echo.
echo Example:
echo   %INSTALL_DIR%\run.bat "beautiful sunset"
echo.
echo Images will be saved to your Downloads folder.
echo =====================================================
echo.
echo Press any key to test...
pause >nul

call "%INSTALL_DIR%\run.bat" "a cute cat"
pause
