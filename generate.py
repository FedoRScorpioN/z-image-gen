#!/usr/bin/env python3
"""
Z-Image Generator - Simple standalone image generator
Optimized for 4GB VRAM (NVIDIA RTX 3050)

Usage:
    python generate.py "your prompt here"
    python generate.py "prompt" --width 1024 --height 576
    python generate.py --interactive
"""

import os
import sys
import random
import datetime
import argparse
import time
from pathlib import Path

# Configuration
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512
DEFAULT_STEPS = 4

# Model URLs
MODEL_URLS = {
    "q4_0": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf",
}
MODEL_SIZES = {
    "q4_0": "3.68 GB",
}


def print_error(msg):
    """Print error message."""
    print(f"\n[ERROR] {msg}\n")


def print_info(msg):
    """Print info message."""
    print(f"[INFO] {msg}")


def print_ok(msg):
    """Print success message."""
    print(f"[OK] {msg}")


def check_dependencies():
    """Check and import dependencies with helpful error messages."""
    global StableDiffusion, Image, tqdm
    
    # Check stable-diffusion-cpp-python
    try:
        from stable_diffusion_cpp import StableDiffusion
    except ImportError:
        print_error("stable-diffusion-cpp-python is not installed!")
        print("To install, run:")
        print("  pip install stable-diffusion-cpp-python")
        print("\nFor CUDA support:")
        print("  set CMAKE_ARGS=-DSD_CUDA=ON")
        print("  pip install stable-diffusion-cpp-python")
        sys.exit(1)
    
    # Check Pillow
    try:
        from PIL import Image
    except ImportError:
        print_error("Pillow is not installed!")
        print("To install, run: pip install pillow")
        sys.exit(1)
    
    # Check tqdm (optional, for download progress)
    try:
        from tqdm import tqdm
    except ImportError:
        tqdm = None


def get_downloads_folder():
    """Get the Windows Downloads folder path."""
    # Try Windows API
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            
            # CoInitialize
            try:
                ctypes.windll.ole32.CoInitialize(None)
            except:
                pass
            
            # Get Downloads folder
            FOLDERID_Downloads = "{374DE290-123F-4565-9164-2C9AA0BAD945}"
            
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
        except Exception:
            pass
    
    # Fallback
    downloads = Path.home() / "Downloads"
    if downloads.exists():
        return downloads
    return Path.home()


def get_model_path():
    """Get the path to the model file, downloading if necessary."""
    # Possible model locations
    possible_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "z-image-gen" / "models" / "z_image_turbo-Q4_0.gguf",
        Path.home() / ".cache" / "z-image-gen" / "models" / "z_image_turbo-Q4_0.gguf",
        Path(__file__).parent / "models" / "z_image_turbo-Q4_0.gguf",
    ]
    
    # Check if model exists (at least 1GB)
    for path in possible_paths:
        try:
            if path.exists() and path.stat().st_size > 1_000_000_000:
                return path
        except:
            continue
    
    # Model not found, need to download
    model_path = possible_paths[0]
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    url = MODEL_URLS["q4_0"]
    size = MODEL_SIZES["q4_0"]
    
    print(f"\n{'='*60}")
    print("Model not found. Downloading Z-Image-Turbo Q4_0...")
    print(f"Size: {size}")
    print("This may take 10-30 minutes depending on your internet...")
    print(f"{'='*60}\n")
    
    try:
        import requests
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(model_path, 'wb') as f:
            if tqdm and total_size > 0:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            pbar.update(len(chunk))
            else:
                print("Downloading... (no progress bar available)")
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        # Show progress every 100MB
                        if downloaded % (100 * 1024 * 1024) == 0:
                            mb = downloaded / (1024 * 1024)
                            print(f"  Downloaded: {mb:.0f} MB")
        
        print(f"\n[OK] Model downloaded to: {model_path}\n")
        return model_path
        
    except Exception as e:
        print_error(f"Download failed: {e}")
        print(f"\nPlease download manually from:")
        print(f"  {url}")
        print(f"And save to: {model_path}")
        sys.exit(1)


def generate_image(
    prompt,
    model_path,
    output_path,
    width=DEFAULT_WIDTH,
    height=DEFAULT_HEIGHT,
    steps=DEFAULT_STEPS,
    seed=-1,
):
    """Generate an image from a prompt."""
    
    # Generate seed if not provided
    if seed < 0:
        seed = random.randint(0, 999999)
    
    print(f"\n{'='*60}")
    print("Generating image...")
    print(f"{'='*60}")
    print(f"Prompt: {prompt}")
    print(f"Size: {width}x{height} | Steps: {steps} | Seed: {seed}")
    print()
    
    try:
        # Initialize with low VRAM settings
        print_info("Loading model (first run may take a minute)...")
        
        sd = StableDiffusion(
            model_path=str(model_path),
            offload_params_to_cpu=True,      # Offload to RAM
            flash_attn=True,                  # Flash attention
            diffusion_flash_attn=True,        # Flash attention for diffusion
            keep_clip_on_cpu=False,           # Keep text encoder on GPU
            keep_vae_on_cpu=True,             # VAE on CPU to save VRAM
            vae_decode_only=True,             # VAE decode only
            verbose=False,
        )
        
        print_info("Model loaded. Generating...")
        start_time = time.time()
        
        # Generate
        images = sd.generate_image(
            prompt=prompt,
            width=width,
            height=height,
            sample_steps=steps,
            seed=seed,
            cfg_scale=0.0,  # Turbo doesn't need guidance
            sample_method="euler_a",
        )
        
        elapsed = time.time() - start_time
        
        if images:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save image
            images[0].save(output_path)
            
            print()
            print_ok(f"Generated in {elapsed:.1f} seconds")
            print_ok(f"Saved to: {output_path}")
            
            # Cleanup
            del sd
            
            return True
        else:
            print_error("Generation failed - no output from model")
            return False
            
    except Exception as e:
        print_error(f"Generation error: {e}")
        return False


def interactive_mode(model_path):
    """Run in interactive mode."""
    print(f"\n{'='*60}")
    print("       Z-Image Generator - Interactive Mode")
    print(f"{'='*60}")
    print("\nEnter prompts to generate images. Type 'quit' to exit.\n")
    
    count = 0
    output_dir = get_downloads_folder()
    
    while True:
        try:
            prompt = input("\nPrompt (or 'quit'): ").strip()
            
            if prompt.lower() in ('quit', 'exit', 'q'):
                break
            
            if not prompt:
                print("Please enter a prompt.")
                continue
            
            # Generate
            seed = random.randint(0, 999999)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"zimage_{seed}_{timestamp}.png"
            
            if generate_image(prompt, model_path, output_path, seed=seed):
                count += 1
                
        except KeyboardInterrupt:
            print("\n\nInterrupted.")
            break
    
    print(f"\nSession ended. Generated {count} image(s).")


def main():
    parser = argparse.ArgumentParser(
        prog="z-image-gen",
        description="Local AI image generation with Z-Image model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate.py "beautiful sunset over mountains"
  python generate.py "cyberpunk city" --width 1024 --height 576
  python generate.py "cat" --seed 42
  python generate.py --interactive
        """,
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Text prompt for image generation",
    )
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=DEFAULT_WIDTH,
        help=f"Image width (default: {DEFAULT_WIDTH})",
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=DEFAULT_HEIGHT,
        help=f"Image height (default: {DEFAULT_HEIGHT})",
    )
    parser.add_argument(
        "-s", "--steps",
        type=int,
        default=DEFAULT_STEPS,
        help=f"Sampling steps (default: {DEFAULT_STEPS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=-1,
        help="Random seed (-1 for random)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path",
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Download model without generating",
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check dependencies
    check_dependencies()
    
    # Get model path
    model_path = get_model_path()
    
    # Just download model
    if args.download_model:
        print_ok(f"Model ready: {model_path}")
        return 0
    
    # Interactive mode
    if args.interactive:
        interactive_mode(model_path)
        return 0
    
    # Need a prompt
    if not args.prompt:
        parser.print_help()
        print("\n" + "="*60)
        print("QUICK START:")
        print("  run.bat \"your prompt here\"")
        print("\nExample:")
        print("  run.bat \"beautiful sunset over mountains\"")
        print("="*60)
        return 0
    
    # Generate single image
    output_dir = get_downloads_folder()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        seed = args.seed if args.seed >= 0 else random.randint(0, 999999)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"zimage_{seed}_{timestamp}.png"
    
    success = generate_image(
        prompt=args.prompt,
        model_path=model_path,
        output_path=output_path,
        width=args.width,
        height=args.height,
        steps=args.steps,
        seed=args.seed,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        sys.exit(1)
