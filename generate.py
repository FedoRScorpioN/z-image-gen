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
from pathlib import Path

# Try imports with helpful error messages
try:
    from stable_diffusion_cpp import StableDiffusion
except ImportError:
    print("Error: stable-diffusion-cpp-python is not installed.")
    print("Please run: pip install stable-diffusion-cpp-python")
    print("With CUDA: CMAKE_ARGS=\"-DSD_CUDA=ON\" pip install stable-diffusion-cpp-python")
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is not installed.")
    print("Please run: pip install pillow")
    sys.exit(1)

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Configuration
DEFAULT_WIDTH = 768
DEFAULT_HEIGHT = 512
DEFAULT_STEPS = 4
DEFAULT_MODEL = "q4_0"

# Model URLs
MODEL_URLS = {
    "q4_0": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf",
    "q5_0": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q5_0.gguf",
    "q8_0": "https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q8_0.gguf",
}

MODEL_SIZES = {
    "q4_0": "3.68 GB",
    "q5_0": "4.54 GB",
    "q8_0": "6.58 GB",
}


def get_model_path(model_type: str = "q4_0") -> Path:
    """Get the path to the model file, downloading if necessary."""
    # Try several locations
    possible_paths = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "z-image-gen" / "models" / f"z_image_turbo-{model_type.upper()}.gguf",
        Path.home() / ".cache" / "z-image-gen" / "models" / f"z_image_turbo-{model_type.upper()}.gguf",
        Path(__file__).parent / "models" / f"z_image_turbo-{model_type.upper()}.gguf",
    ]
    
    # Check if model exists
    for path in possible_paths:
        if path.exists() and path.stat().st_size > 1000000:  # At least 1MB
            return path
    
    # Model not found, need to download
    model_path = possible_paths[0]
    model_path.parent.mkdir(parents=True, exist_ok=True)
    
    url = MODEL_URLS.get(model_type, MODEL_URLS["q4_0"])
    size = MODEL_SIZES.get(model_type, MODEL_SIZES["q4_0"])
    
    print(f"\nModel not found. Downloading Z-Image-Turbo {model_type.upper()}...")
    print(f"Size: {size}")
    print(f"This may take a while...\n")
    
    try:
        import requests
        from tqdm import tqdm
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f:
            with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        print(f"\nModel downloaded to: {model_path}\n")
        return model_path
        
    except Exception as e:
        print(f"\nError downloading model: {e}")
        print(f"\nPlease download manually from:")
        print(f"  {url}")
        print(f"And save to: {model_path}")
        sys.exit(1)


def get_output_dir() -> Path:
    """Get the output directory (Downloads folder)."""
    # Try to get Windows Downloads folder
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            
            FOLDERID_Downloads = "{374DE290-123F-4565-9164-2C9AA0BAD945}"
            
            ctypes.windll.ole32.CoInitialize(None)
            
            SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.c_char_p,
                wintypes.DWORD,
                wintypes.HANDLE,
                ctypes.POINTER(ctypes.c_wchar_p)
            ]
            SHGetKnownFolderPath.restype = ctypes.HRESULT
            
            pszPath = ctypes.c_wchar_p()
            hr = SHGetKnownFolderPath(
                FOLDERID_Downloads.encode('utf-8'),
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


def generate_image(
    prompt: str,
    model_path: Path,
    output_path: Path,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
    steps: int = DEFAULT_STEPS,
    seed: int = -1,
    negative_prompt: str = "",
) -> bool:
    """Generate an image from a prompt."""
    
    console = Console() if RICH_AVAILABLE else None
    
    # Generate seed if not provided
    if seed < 0:
        seed = random.randint(0, 999999)
    
    if console:
        console.print(f"\n[bold blue]Generating image...[/bold blue]")
        console.print(f"[dim]Prompt: {prompt}[/dim]")
        console.print(f"[dim]Size: {width}x{height} | Steps: {steps} | Seed: {seed}[/dim]")
    else:
        print(f"\nGenerating image...")
        print(f"Prompt: {prompt}")
        print(f"Size: {width}x{height} | Steps: {steps} | Seed: {seed}")
    
    try:
        # Initialize with low VRAM settings
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
        
        start_time = datetime.datetime.now()
        
        # Generate
        images = sd.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            sample_steps=steps,
            seed=seed,
            cfg_scale=0.0,  # Turbo doesn't need guidance
            sample_method="euler_a",
        )
        
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        
        if images:
            # Save image
            output_path.parent.mkdir(parents=True, exist_ok=True)
            images[0].save(output_path)
            
            if console:
                console.print(f"\n[bold green]✓ Generated in {elapsed:.1f}s[/bold green]")
                console.print(f"[green]✓ Saved to: {output_path}[/green]")
            else:
                print(f"\n✓ Generated in {elapsed:.1f}s")
                print(f"✓ Saved to: {output_path}")
            
            # Cleanup
            del sd
            
            return True
        else:
            if console:
                console.print("[red]✗ Generation failed - no output[/red]")
            else:
                print("✗ Generation failed - no output")
            return False
            
    except Exception as e:
        if console:
            console.print(f"[red]✗ Error: {e}[/red]")
        else:
            print(f"✗ Error: {e}")
        return False


def interactive_mode(model_path: Path):
    """Run in interactive mode."""
    console = Console() if RICH_AVAILABLE else None
    
    if console:
        console.print("\n[bold]═══════════════════════════════════════════════════════════[/bold]")
        console.print("[bold]           Z-Image Generator - Interactive Mode[/bold]")
        console.print("[bold]═══════════════════════════════════════════════════════════[/bold]")
        console.print("\nEnter prompts to generate images. Type 'quit' to exit.\n")
    else:
        print("\n" + "=" * 60)
        print("           Z-Image Generator - Interactive Mode")
        print("=" * 60)
        print("\nEnter prompts to generate images. Type 'quit' to exit.\n")
    
    count = 0
    output_dir = get_output_dir()
    
    while True:
        try:
            if RICH_AVAILABLE:
                from rich.prompt import Prompt
                prompt = Prompt.ask("\n[cyan]Prompt[/cyan]").strip()
            else:
                prompt = input("\nPrompt: ").strip()
            
            if prompt.lower() in ('quit', 'exit', 'q'):
                break
            
            if not prompt:
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
    
    if console:
        console.print(f"\n[bold]Session ended. Generated {count} image(s).[/bold]")
    else:
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
        "-m", "--model",
        choices=["q4_0", "q5_0", "q8_0"],
        default="q4_0",
        help="Model quantization (default: q4_0 for 4GB VRAM)",
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
    
    args = parser.parse_args()
    
    # Get model path
    model_path = get_model_path(args.model)
    
    # Just download model
    if args.download_model:
        print(f"Model ready: {model_path}")
        return 0
    
    # Interactive mode
    if args.interactive:
        interactive_mode(model_path)
        return 0
    
    # Need a prompt
    if not args.prompt:
        parser.print_help()
        return 0
    
    # Generate single image
    output_dir = get_output_dir()
    
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
    sys.exit(main())
