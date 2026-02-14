@echo off
chcp 65001 >nul
title Z-Image Generator - Auto Installer

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║           Z-Image Generator - Auto Installer                  ║
echo ║           Optimized for 4GB VRAM                              ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

:: Check for admin rights (needed for some installations)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Requesting administrator privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Set installation directory
set "INSTALL_DIR=%LOCALAPPDATA%\z-image-gen"
set "MODEL_DIR=%INSTALL_DIR%\models"
set "VENV_DIR=%INSTALL_DIR%\venv"

echo [*] Installation directory: %INSTALL_DIR%
echo.

:: Step 1: Check Python
echo [1/6] Checking Python installation...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Python not found. Installing Python 3.11...
    
    :: Download Python installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe' -OutFile '%TEMP%\python_installer.exe'}"
    
    :: Install Python silently with pip and CUDA support options
    echo [*] Installing Python (this may take a minute)...
    %TEMP%\python_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_pip=1 Include_test=0
    timeout /t 60 /nobreak >nul
    
    :: Refresh environment
    call refreshenv >nul 2>&1
    
    python --version >nul 2>&1
    if %errorLevel% neq 0 (
        echo [ERROR] Python installation failed!
        echo Please install Python manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)
echo [✓] Python found:
python --version
echo.

:: Step 2: Check NVIDIA GPU and CUDA
echo [2/6] Checking NVIDIA GPU...
nvidia-smi >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] NVIDIA GPU not detected or drivers not installed!
    echo [!] This tool requires an NVIDIA GPU with CUDA support.
    echo.
    echo Please install NVIDIA drivers from: https://www.nvidia.com/Download/index.aspx
    pause
    exit /b 1
)
echo [✓] NVIDIA GPU detected:
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
echo.

:: Step 3: Create installation directory
echo [3/6] Creating installation directory...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%"
echo [✓] Directory created: %INSTALL_DIR%
echo.

:: Step 4: Create virtual environment
echo [4/6] Setting up Python environment...
if not exist "%VENV_DIR%" (
    python -m venv "%VENV_DIR%"
    echo [✓] Virtual environment created
) else (
    echo [✓] Virtual environment already exists
)

:: Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

:: Upgrade pip
python -m pip install --upgrade pip --quiet
echo.

:: Step 5: Install dependencies
echo [5/6] Installing dependencies...
echo [*] This may take several minutes on first run...
echo.

:: Install PyTorch with CUDA support first
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 --quiet

:: Install stable-diffusion-cpp-python with CUDA
set CMAKE_ARGS=-DSD_CUDA=ON
pip install cmake --quiet
pip install stable-diffusion-cpp-python --quiet

:: Install other dependencies
pip install requests rich pillow platformdirs tqdm huggingface-hub --quiet

echo [✓] Dependencies installed
echo.

:: Step 6: Download model
echo [6/6] Downloading Z-Image-Turbo model (Q4_0)...
echo [*] Model size: ~3.68 GB
echo [*] This may take a while depending on your internet connection...
echo.

set "MODEL_PATH=%MODEL_DIR%\z_image_turbo-Q4_0.gguf"
set "MODEL_URL=https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf"

if exist "%MODEL_PATH%" (
    echo [✓] Model already downloaded
) else (
    echo [*] Downloading model...
    powershell -Command "& {"
    powershell -Command "  $ProgressPreference = 'SilentlyContinue'"
    powershell -Command "  Write-Host 'Downloading Z-Image-Turbo Q4_0 model...'"
    powershell -Command "  Invoke-WebRequest -Uri '%MODEL_URL%' -OutFile '%MODEL_PATH%' -UseBasicParsing"
    powershell -Command "  Write-Host 'Download complete!'"
    powershell -Command "}"
    
    if not exist "%MODEL_PATH%" (
        echo [ERROR] Model download failed!
        echo Please check your internet connection and try again.
        pause
        exit /b 1
    )
)
echo [✓] Model ready
echo.

:: Create launcher scripts
echo [*] Creating launcher scripts...

:: Create run.bat
(
echo @echo off
echo chcp 65001 ^>nul
echo call "%VENV_DIR%\Scripts\activate.bat"
echo python "%INSTALL_DIR%\generate.py" %%*
) > "%INSTALL_DIR%\run.bat"

:: Create generate.py
(
echo """Z-Image Generator - Simple launcher"""
echo import sys
echo import os
echo 
echo # Add to path
echo sys.path.insert(0, r'%INSTALL_DIR%\src')
echo 
echo # Model path
echo MODEL_PATH = r'%MODEL_PATH%'
echo 
echo def main^(^):
echo     if len(sys.argv) ^< 2:
echo         print^("Usage: run.bat \"your prompt here\""^)
echo         print^("   or: run.bat --interactive"^)
echo         return
echo     
echo     # Import after checking args
echo     from stable_diffusion_cpp import StableDiffusion
echo     from PIL import Image
echo     import datetime
echo     from pathlib import Path
echo     
echo     # Parse arguments
echo     if sys.argv[1] == "--interactive":
echo         print^("Interactive mode - coming soon!"^)
echo         print^("For now, use: run.bat \"your prompt\""^)
echo         return
echo     
echo     prompt = sys.argv[1]
echo     output_dir = Path.home^(^) / "Downloads"
echo     
echo     # Generate timestamp and seed
echo     timestamp = datetime.datetime.now^(^).strftime^("%%Y%%m%%d_%%H%%M%%S"^)
echo     import random
echo     seed = random.randint^(0, 999999^)
echo     
echo     output_path = output_dir / f"zimage_{seed}_{timestamp}.png"
echo     
echo     print^(f"\nGenerating image..."^)
echo     print^(f"Prompt: {prompt}"^)
echo     print^(f"Output: {output_path}"^)
echo     print^(^)
echo     
echo     # Initialize generator with low VRAM settings
echo     sd = StableDiffusion^(
echo         model_path=MODEL_PATH,
echo         offload_params_to_cpu=True,
echo         flash_attn=True,
echo         diffusion_flash_attn=True,
echo         keep_clip_on_cpu=False,
echo         keep_vae_on_cpu=True,
echo         vae_decode_only=True,
echo         verbose=False,
echo     ^)
echo     
echo     # Generate
echo     import time
echo     start = time.time^(^)
echo     
echo     images = sd.generate_image^(
echo         prompt=prompt,
echo         width=768,
echo         height=512,
echo         sample_steps=4,
echo         seed=seed,
echo         cfg_scale=0.0,
echo         sample_method="euler_a",
echo     ^)
echo     
echo     elapsed = time.time^(^) - start
echo     
echo     if images:
echo         images[0].save^(output_path^)
echo         print^(f"✓ Generated in {elapsed:.1f}s"^)
echo         print^(f"✓ Saved to: {output_path}"^)
echo     else:
echo         print^("✗ Generation failed"^)
echo     
echo     # Cleanup
echo     del sd
echo 
echo if __name__ == "__main__":
echo     main^(^)
) > "%INSTALL_DIR%\generate.py"

:: Copy source files
xcopy /E /I /Y "%~dp0src" "%INSTALL_DIR%\src" >nul 2>&1

echo [✓] Launcher scripts created
echo.

:: Create desktop shortcut
echo [*] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut([System.IO.Path]::Combine([Environment]::GetFolderPath('Desktop'), 'Z-Image-Gen.lnk')); $Shortcut.TargetPath = '%INSTALL_DIR%\run.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = 'Z-Image Generator'; $Shortcut.Save()"

echo.
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                    INSTALLATION COMPLETE!                     ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.
echo   Installation directory: %INSTALL_DIR%
echo   Model location: %MODEL_PATH%
echo.
echo   USAGE:
echo   ─────────────────────────────────────────────────────────────
echo   1. Open Command Prompt or PowerShell
echo   2. Run: "%INSTALL_DIR%\run.bat" "your prompt here"
echo.
echo   Example:
echo      "%INSTALL_DIR%\run.bat" "beautiful sunset over mountains"
echo.
echo   Or double-click the desktop shortcut: Z-Image-Gen
echo.
echo   Images will be saved to your Downloads folder.
echo ═══════════════════════════════════════════════════════════════
echo.
echo Press any key to test the installation...
pause >nul

:: Test run
echo.
echo [*] Running test generation...
echo [*] This may take a minute on first run...
echo.
call "%INSTALL_DIR%\run.bat" "test image of a cat"

echo.
echo ═══════════════════════════════════════════════════════════════
echo Installation complete! Check your Downloads folder for the test image.
echo ═══════════════════════════════════════════════════════════════
pause
