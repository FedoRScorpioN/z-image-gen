#!/usr/bin/env python3
"""
Z-Image Generator - Using sd-cli.exe from stable-diffusion.cpp
Works on 4GB VRAM (RTX 3050)
"""

import os
import sys
import subprocess
import datetime
import argparse
import random
from pathlib import Path

# Configuration
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512

# URLs
SD_CLI_URL = "https://github.com/leejet/stable-diffusion.cpp/releases/download/master-504-636d3cb/sd-master-636d3cb-bin-win-cuda12-x64.zip"
CUDA_DLL_URL = "https://github.com/leejet/stable-diffusion.cpp/releases/download/master-504-636d3cb/cudart-sd-bin-win-cu12-x64.zip"

# Model URLs (correct sources)
MODEL_URLS = {
    "diffusion": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf",
    "vae": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors",
    "llm": "https://huggingface.co/unsloth/Qwen3-4B-Instruct-2507-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
}


def get_base_path():
    """Get installation directory."""
    if sys.platform == "win32":
        return Path(os.environ.get("LOCALAPPDATA", "")) / "z-image-gen"
    return Path.home() / ".local" / "z-image-gen"


def get_downloads_folder():
    """Get Windows Downloads folder."""
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            
            FOLDERID_Downloads = "{374DE290-123F-4565-9164-2C9AA0BAD945}"
            
            try:
                ctypes.windll.ole32.CoInitialize(None)
            except:
                pass
            
            SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.c_wchar_p,
                wintypes.DWORD,
                wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_wchar_p)
            ]
            SHGetKnownFolderPath.restype = ctypes.HRESULT
            
            pszPath = ctypes.c_wchar_p()
            hr = SHGetKnownFolderPath(
                ctypes.c_wchar_p(FOLDERID_Downloads),
                0,
                None,
                ctypes.byref(pszPath)
            )
            
            if hr == 0 and pszPath.value:
                return Path(pszPath.value)
        except:
            pass
    
    downloads = Path.home() / "Downloads"
    if downloads.exists():
        return downloads
    return Path.home()


def download_file(url, dest, name="file"):
    """Download a file with progress."""
    import requests
    
    print(f"\nDownloading {name}...")
    print(f"  URL: {url}")
    print(f"  To: {dest}")
    
    dest.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest, 'wb') as f:
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        pct = (downloaded / total) * 100
                        print(f"\r  Progress: {mb:.1f} / {total_mb:.1f} MB ({pct:.0f}%)", end="", flush=True)
        
        print(f"\n  Done! ({downloaded / (1024*1024):.1f} MB)")
        return True
        
    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False


def find_sd_cli(base):
    """Find sd-cli.exe in the installation."""
    bin_dir = base / "bin"
    
    # Expected locations
    possible = [
        bin_dir / "Release" / "sd-cli.exe",
        bin_dir / "sd-cli.exe",
        bin_dir / "build" / "bin" / "Release" / "sd-cli.exe",
    ]
    
    for p in possible:
        if p.exists():
            return p
    
    # Search recursively
    if bin_dir.exists():
        for f in bin_dir.rglob("sd-cli.exe"):
            return f
    
    return None


def check_installation():
    """Check if all required files exist."""
    base = get_base_path()
    
    sd_cli = find_sd_cli(base)
    diffusion = base / "models" / "z_image_turbo-Q4_0.gguf"
    vae = base / "models" / "ae.safetensors"
    llm = base / "models" / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    cudart = base / "bin" / "cudart_12.dll"
    
    print("\nChecking installation...")
    all_ok = True
    
    # Check sd-cli
    if sd_cli:
        size_mb = sd_cli.stat().st_size / (1024 * 1024)
        print(f"  [OK] sd-cli.exe: {size_mb:.1f} MB ({sd_cli.relative_to(base)})")
    else:
        print(f"  [MISSING] sd-cli.exe")
        all_ok = False
    
    # Check CUDA runtime
    if cudart.exists():
        size_mb = cudart.stat().st_size / (1024 * 1024)
        print(f"  [OK] CUDA runtime: {size_mb:.1f} MB")
    else:
        print(f"  [MISSING] cudart_12.dll - run with --install")
        all_ok = False
    
    # Check models
    for name, path in [
        ("diffusion model", diffusion),
        ("VAE", vae),
        ("LLM/text encoder", llm),
    ]:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {name}: {size_mb:.1f} MB")
        else:
            print(f"  [MISSING] {name}")
            all_ok = False
    
    return all_ok


def install():
    """Download and install all required files."""
    import requests
    import zipfile
    
    base = get_base_path()
    bin_dir = base / "bin"
    models_dir = base / "models"
    
    bin_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Z-Image Generator - Installation")
    print("=" * 60)
    
    # Download sd-cli
    sd_cli = find_sd_cli(base)
    if not sd_cli:
        print("\n[1/5] Downloading sd-cli (CUDA 12 for Windows)...")
        zip_path = base / "sd-cli.zip"

        if not download_file(SD_CLI_URL, zip_path, "stable-diffusion.cpp"):
            print("Failed to download sd-cli!")
            return False

        print("\nExtracting...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(bin_dir)
            zip_path.unlink()
            print("  Done!")
        except Exception as e:
            print(f"  ERROR extracting: {e}")
            return False

        sd_cli = find_sd_cli(base)
        if sd_cli:
            print(f"  Found sd-cli.exe at: {sd_cli.relative_to(base)}")
        else:
            print("  Contents of bin directory:")
            for f in bin_dir.rglob("*"):
                if f.is_file():
                    print(f"    {f.relative_to(bin_dir)}")
    else:
        print(f"\n[1/5] sd-cli.exe already exists")

    # Download CUDA runtime DLLs
    cudart_dll = bin_dir / "cudart_12.dll"
    if not cudart_dll.exists():
        print("\n[2/5] Downloading CUDA runtime DLLs...")
        cuda_zip = base / "cuda-dlls.zip"

        if not download_file(CUDA_DLL_URL, cuda_zip, "CUDA runtime"):
            print("Failed to download CUDA DLLs!")
            return False

        print("\nExtracting CUDA DLLs...")
        try:
            with zipfile.ZipFile(cuda_zip, 'r') as zf:
                zf.extractall(bin_dir)
            cuda_zip.unlink()
            print("  Done!")
        except Exception as e:
            print(f"  ERROR extracting CUDA DLLs: {e}")
            return False
    else:
        print(f"\n[2/5] CUDA runtime DLLs already exist")
    
    # Download models
    models = [
        ("diffusion model", MODEL_URLS["diffusion"], "z_image_turbo-Q4_0.gguf"),
        ("VAE", MODEL_URLS["vae"], "ae.safetensors"),
        ("LLM/text encoder", MODEL_URLS["llm"], "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"),
    ]

    for i, (name, url, filename) in enumerate(models, 3):
        dest = models_dir / filename

        if dest.exists() and dest.stat().st_size > 1000000:
            size_mb = dest.stat().st_size / (1024 * 1024)
            print(f"\n[{i}/5] {name} already exists ({size_mb:.0f} MB)")
        else:
            print(f"\n[{i}/5] Downloading {name}...")
            if not download_file(url, dest, name):
                print(f"  WARNING: Failed to download {name}")
    
    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)
    
    check_installation()
    return True


def generate(prompt, output_path=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, seed=-1, return_path=False):
    """Generate an image using sd-cli.exe."""
    base = get_base_path()
    models_dir = base / "models"
    
    sd_cli = find_sd_cli(base)
    diffusion = models_dir / "z_image_turbo-Q4_0.gguf"
    vae = models_dir / "ae.safetensors"
    llm = models_dir / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    
    # Check files exist
    if not sd_cli:
        print("ERROR: sd-cli.exe not found. Run with --install first.")
        return False
    
    if not diffusion.exists():
        print(f"ERROR: Diffusion model not found: {diffusion}")
        return False
    
    if not vae.exists():
        print(f"ERROR: VAE not found: {vae}")
        return False
    
    if not llm.exists():
        print(f"ERROR: LLM not found: {llm}")
        return False
    
    # Output path
    if output_path is None:
        downloads = get_downloads_folder()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        if seed < 0:
            seed = random.randint(0, 999999)
        output_path = downloads / f"zimage_{seed}_{timestamp}.png"
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating image...")
    print(f"  Prompt: {prompt}")
    print(f"  Size: {width}x{height}")
    print(f"  Seed: {seed}")
    print(f"  Output: {output_path}")
    print()
    
    # Build command - optimized for 4GB VRAM
    cmd = [
        str(sd_cli),
        "--diffusion-model", str(diffusion),
        "--vae", str(vae),
        "--llm", str(llm),
        "-p", prompt,
        "--cfg-scale", "1.0",
        "--offload-to-cpu",
        "--diffusion-fa",
        "--vae-tiling",
        "--clip-on-cpu",
        "-W", str(width),
        "-H", str(height),
        "-o", str(output_path),
    ]
    
    if seed >= 0:
        cmd.extend(["--seed", str(seed)])
    
    start = datetime.datetime.now()
    
    try:
        print("Running sd-cli...")
        result = subprocess.run(cmd, cwd=str(sd_cli.parent))
        
        elapsed = (datetime.datetime.now() - start).total_seconds()
        
        if output_path.exists():
            print(f"\n[OK] Generated in {elapsed:.1f}s")
            print(f"Saved to: {output_path}")
            if return_path:
                return True, output_path
            return True
        else:
            print(f"\n[ERROR] Output file not created")
            if return_path:
                return False, None
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        if return_path:
            return False, None
        return False


def interactive_mode(width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
    """Interactive mode - generate images in a loop."""
    print("\n" + "=" * 60)
    print("  Z-Image Generator - Interactive Mode")
    print("=" * 60)
    print(f"\nImage size: {width}x{height}")
    print("\nCommands:")
    print("  <prompt>    - Generate image from text")
    print("  size WxH    - Change size (e.g., size 1024x576)")
    print("  check       - Check installation")
    print("  help        - Show this help")
    print("  quit/exit   - Exit program")
    print("\nImages are saved to your Downloads folder.")
    print("-" * 60)
    
    generated_count = 0
    last_output = None
    
    while True:
        try:
            print()
            prompt = input("Enter prompt> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye!")
            break
        
        if not prompt:
            continue
        
        # Commands
        if prompt.lower() in ('quit', 'exit', 'q'):
            print(f"\nGenerated {generated_count} image(s). Goodbye!")
            break
        
        if prompt.lower() == 'help':
            print("\nCommands:")
            print("  <prompt>    - Generate image from text")
            print("  size WxH    - Change size (e.g., size 1024x576)")
            print("  check       - Check installation")
            print("  help        - Show this help")
            print("  quit/exit   - Exit program")
            continue
        
        if prompt.lower() == 'check':
            check_installation()
            continue
        
        if prompt.lower().startswith('size '):
            try:
                size_part = prompt[5:].strip().lower()
                if 'x' in size_part:
                    w, h = size_part.split('x')
                    width = int(w.strip())
                    height = int(h.strip())
                    print(f"Size changed to {width}x{height}")
                else:
                    print("Usage: size 1024x576")
            except:
                print("Invalid size. Usage: size 1024x576")
            continue
        
        # Generate image
        print("\n" + "-" * 60)
        success, output_path = generate(
            prompt=prompt,
            width=width,
            height=height,
            return_path=True
        )
        
        if success:
            generated_count += 1
            last_output = output_path
            print("\n" + "=" * 60)
            print(f"  SAVED: {output_path}")
            print("=" * 60)
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Z-Image Generator - Local AI image generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py "beautiful sunset over mountains"
  python generate.py "cyberpunk city" --width 1024 --height 576
  python generate.py --install
  python generate.py --check
  python generate.py --interactive
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="Text prompt")
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("-H", "--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("-o", "--output", help="Output path")
    parser.add_argument("--install", action="store_true", help="Download all files")
    parser.add_argument("--check", action="store_true", help="Check installation")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if args.check:
        ok = check_installation()
        return 0 if ok else 1
    
    if args.install:
        ok = install()
        return 0 if ok else 1
    
    # Interactive mode
    if args.interactive or not args.prompt:
        if not check_installation():
            print("\nMissing files! Run: python generate.py --install")
            return 1
        return interactive_mode(width=args.width, height=args.height)
    
    if not check_installation():
        print("\nMissing files! Run: python generate.py --install")
        return 1
    
    success = generate(
        prompt=args.prompt,
        output_path=args.output,
        width=args.width,
        height=args.height,
        seed=args.seed,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
