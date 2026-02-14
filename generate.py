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

# URLs - Windows CUDA 12 build
SD_CLI_URL = "https://github.com/leejet/stable-diffusion.cpp/releases/download/master-504-636d3cb/cudart-sd-bin-win-cu12-x64.zip"

# Model URLs from HuggingFace
MODEL_URLS = {
    "diffusion": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf",
    "vae": "https://huggingface.co/leejet/Z-Image-GGUF/resolve/main/ae.safetensors", 
    "llm": "https://huggingface.co/leejet/Z-Image-GGUF/resolve/main/Qwen3-4B-Instruct-2507-Q4_K_M.gguf",
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


def check_installation():
    """Check if all required files exist."""
    base = get_base_path()
    
    # Look for sd-cli.exe in different possible locations
    possible_sd_cli = [
        base / "bin" / "Release" / "sd-cli.exe",
        base / "bin" / "sd-cli.exe",
        base / "bin" / "build" / "bin" / "Release" / "sd-cli.exe",
    ]
    
    sd_cli = None
    for p in possible_sd_cli:
        if p.exists():
            sd_cli = p
            break
    
    diffusion = base / "models" / "z_image_turbo-Q4_0.gguf"
    vae = base / "models" / "ae.safetensors"
    llm = base / "models" / "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"
    
    print("\nChecking installation...")
    all_ok = True
    
    # Check sd-cli
    if sd_cli:
        size_mb = sd_cli.stat().st_size / (1024 * 1024)
        print(f"  [OK] sd-cli.exe: {size_mb:.1f} MB ({sd_cli.relative_to(base)})")
    else:
        print(f"  [MISSING] sd-cli.exe")
        all_ok = False
    
    # Check models
    for name, path in [("diffusion model", diffusion), ("VAE", vae), ("LLM", llm)]:
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {name}: {size_mb:.1f} MB")
        else:
            print(f"  [MISSING] {name}")
            all_ok = False
    
    return all_ok


def find_sd_cli(base):
    """Find sd-cli.exe in the installation."""
    possible = [
        base / "bin" / "Release" / "sd-cli.exe",
        base / "bin" / "sd-cli.exe",
    ]
    
    # Search recursively
    bin_dir = base / "bin"
    if bin_dir.exists():
        for f in bin_dir.rglob("sd-cli.exe"):
            return f
    
    for p in possible:
        if p.exists():
            return p
    
    return None


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
        print("\n[1/4] Downloading sd-cli (CUDA 12 for Windows)...")
        zip_path = base / "sd-cli.zip"
        
        if not download_file(SD_CLI_URL, zip_path, "stable-diffusion.cpp binaries"):
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
        
        # Find where sd-cli.exe ended up
        sd_cli = find_sd_cli(base)
        if sd_cli:
            print(f"  Found at: {sd_cli.relative_to(base)}")
        else:
            print("  WARNING: sd-cli.exe not found after extraction!")
            print("  Contents of bin directory:")
            for f in bin_dir.rglob("*"):
                if f.is_file():
                    print(f"    {f.relative_to(bin_dir)}")
    else:
        print(f"\n[1/4] sd-cli.exe already exists at {sd_cli.relative_to(base)}")
    
    # Download models
    models = [
        ("diffusion model", "diffusion", MODEL_URLS["diffusion"], "z_image_turbo-Q4_0.gguf"),
        ("VAE", "vae", MODEL_URLS["vae"], "ae.safetensors"),
        ("LLM encoder", "llm", MODEL_URLS["llm"], "Qwen3-4B-Instruct-2507-Q4_K_M.gguf"),
    ]
    
    for i, (name, key, url, filename) in enumerate(models, 2):
        dest = models_dir / filename
        
        if dest.exists() and dest.stat().st_size > 1000000:
            print(f"\n[{i}/4] {name} already exists")
        else:
            print(f"\n[{i}/4] Downloading {name}...")
            if not download_file(url, dest, name):
                print(f"  WARNING: Failed to download {name}")
    
    print("\n" + "=" * 60)
    print("Installation complete!")
    print("=" * 60)
    
    # Verify
    check_installation()
    
    return True


def generate(prompt, output_path=None, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT, seed=-1):
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
        "--offload-to-cpu",      # Offload weights to RAM
        "--diffusion-fa",        # Flash attention
        "--vae-tiling",          # Tiled VAE for low VRAM
        "--clip-on-cpu",         # Keep CLIP on CPU
        "-W", str(width),
        "-H", str(height),
        "-o", str(output_path),
    ]
    
    if seed >= 0:
        cmd.extend(["--seed", str(seed)])
    
    # Run
    start = datetime.datetime.now()
    
    try:
        print("Running sd-cli...")
        result = subprocess.run(cmd, cwd=str(sd_cli.parent))
        
        elapsed = (datetime.datetime.now() - start).total_seconds()
        
        if output_path.exists():
            print(f"\n[OK] Generated in {elapsed:.1f}s")
            print(f"Saved to: {output_path}")
            return True
        else:
            print(f"\n[ERROR] Output file not created")
            return False
            
    except Exception as e:
        print(f"\n[ERROR] {e}")
        return False


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
        """
    )
    
    parser.add_argument("prompt", nargs="?", help="Text prompt")
    parser.add_argument("-w", "--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("-H", "--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--seed", type=int, default=-1)
    parser.add_argument("-o", "--output", help="Output path")
    parser.add_argument("--install", action="store_true", help="Download all files")
    parser.add_argument("--check", action="store_true", help="Check installation")
    
    args = parser.parse_args()
    
    if args.check:
        ok = check_installation()
        return 0 if ok else 1
    
    if args.install:
        ok = install()
        return 0 if ok else 1
    
    if not args.prompt:
        parser.print_help()
        print("\nRun 'python generate.py --install' first to download required files.")
        return 0
    
    # Check installation
    if not check_installation():
        print("\nMissing files! Run: python generate.py --install")
        return 1
    
    # Generate
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
