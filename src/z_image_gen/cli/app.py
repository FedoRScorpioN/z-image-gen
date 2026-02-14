"""
CLI application for z-image-gen
"""

import argparse
import sys
import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from z_image_gen import __version__
from z_image_gen.core.generator import ZImageGenerator, GenerationError
from z_image_gen.core.model import ModelManager, DownloadError
from z_image_gen.config.settings import Settings
from z_image_gen.config.paths import get_downloads_folder, get_model_cache_path

console = Console()


def print_banner():
    """Print the application banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██╗███████╗    ███████╗███████╗ ██████╗ ██████╗ ██████╗   ║
    ║     ╚═╝██╔════╝    ╚══███╔╝██╔════╝██╔═══██╗██╔══██╗██╔══██╗  ║
    ║     ██║███████╗      ███╔╝ █████╗  ██║   ██║██║  ██║██║  ██║  ║
    ║     ██║╚════██║     ███╔╝  ██╔══╝  ██║   ██║██║  ██║██║  ██║  ║
    ║     ██║███████║    ███████╗███████╗╚██████╔╝██████╔╝██████╔╝  ║
    ║     ╚═╝╚══════╝    ╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═════╝   ║
    ║                                                               ║
    ║          Local Image Generator v{:<8}                      ║
    ║          Optimized for 4GB VRAM                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """.format(__version__)
    
    console.print(banner, style="bold blue")


def print_system_info():
    """Print system information"""
    from z_image_gen.config.paths import get_model_cache_path
    
    console.print("\n[bold]System Information:[/bold]")
    console.print(f"  Model cache: {get_model_cache_path()}")
    console.print(f"  Output dir:  {get_downloads_folder()}")
    
    # Check for CUDA
    try:
        import torch
        if torch.cuda.is_available():
            console.print(f"  GPU:         {torch.cuda.get_device_name(0)}")
            console.print(f"  VRAM:        {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        else:
            console.print("  GPU:         [yellow]CUDA not available[/yellow]")
    except ImportError:
        console.print("  GPU:         [dim]PyTorch not installed[/dim]")


def generate_image(
    prompt: str,
    settings: Settings,
    seed: int = -1,
    output: Optional[Path] = None,
) -> Path:
    """
    Generate and save an image.
    
    Args:
        prompt: Text prompt
        settings: Generation settings
        seed: Random seed (-1 for random)
        output: Output path (auto-generated if None)
    
    Returns:
        Path to saved image
    """
    try:
        with ZImageGenerator(
            model_type=settings.model_type,
            settings=settings,
        ) as generator:
            # Generate
            image = generator.generate(
                prompt=prompt,
                width=settings.width,
                height=settings.height,
                steps=settings.steps,
                seed=seed,
            )
            
            if image is None:
                console.print("[red]Failed to generate image[/red]")
                return None
            
            # Determine output path
            if output is None:
                output = settings.get_output_path(seed=seed)
            
            # Save image
            image.save(output)
            console.print(f"\n[bold green]✓ Image saved![/bold green]")
            console.print(f"  Path: {output}")
            console.print(f"  Size: {settings.width}x{settings.height}")
            
            return output
            
    except GenerationError as e:
        console.print(f"[red]Generation error: {e}[/red]")
        return None
    except DownloadError as e:
        console.print(f"[red]Download error: {e}[/red]")
        return None


def interactive_mode(settings: Settings):
    """Run in interactive mode"""
    print_banner()
    print_system_info()
    
    console.print("\n[bold]Interactive Mode[/bold]")
    console.print("Enter prompts to generate images. Type 'quit' to exit.\n")
    
    count = 0
    
    while True:
        try:
            prompt = Prompt.ask("\n[cyan]Prompt[/cyan] (or 'quit')").strip()
            
            if prompt.lower() in ('quit', 'exit', 'q'):
                break
            
            if not prompt:
                console.print("[yellow]Please enter a prompt.[/yellow]")
                continue
            
            # Generate with random seed
            output = generate_image(prompt, settings, seed=-1)
            
            if output:
                count += 1
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted.[/yellow]")
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
    
    console.print(f"\n[bold]Session ended.[/bold] Generated {count} image(s).")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        prog="z-image-gen",
        description="Local AI image generation with Z-Image model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  z-image-gen "a beautiful sunset over mountains"
  z-image-gen "cyberpunk city" --width 1024 --height 576
  z-image-gen "cat" --seed 42 --output ./my_image.png
  z-image-gen --interactive
        """,
    )
    
    # Positional argument for prompt
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Text prompt for image generation",
    )
    
    # Generation options
    parser.add_argument(
        "-w", "--width",
        type=int,
        default=768,
        help="Image width (default: 768)",
    )
    parser.add_argument(
        "-H", "--height",
        type=int,
        default=512,
        help="Image height (default: 512)",
    )
    parser.add_argument(
        "-s", "--steps",
        type=int,
        default=4,
        help="Sampling steps (default: 4 for Turbo)",
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
    
    # Output options
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file path",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: Downloads)",
    )
    
    # Mode options
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Run in interactive mode",
    )
    
    # Utility commands
    parser.add_argument(
        "--download-model",
        action="store_true",
        help="Download model without generating",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show system information",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"z-image-gen {__version__}",
    )
    
    args = parser.parse_args()
    
    # Utility commands
    if args.list_models:
        console.print("\n[bold]Available Models:[/bold]\n")
        for model in ModelManager.list_available_models():
            console.print(f"  [cyan]{model['type']}[/cyan]: {model['name']}")
            console.print(f"    Size: {model['size_gb']:.2f} GB")
            console.print(f"    Recommended VRAM: {model['recommended_vram']}")
        return 0
    
    if args.info:
        print_banner()
        print_system_info()
        return 0
    
    if args.download_model:
        print_banner()
        manager = ModelManager(args.model)
        if manager.is_downloaded():
            console.print(f"[green]Model already downloaded: {manager.model_path}[/green]")
        else:
            manager.download()
        return 0
    
    # Create settings
    settings = Settings(
        model_type=args.model,
        width=args.width,
        height=args.height,
        steps=args.steps,
        output_dir=args.output_dir,
    )
    
    # Interactive mode
    if args.interactive:
        interactive_mode(settings)
        return 0
    
    # Single prompt mode
    if args.prompt:
        print_banner()
        output = generate_image(
            prompt=args.prompt,
            settings=settings,
            seed=args.seed,
            output=args.output,
        )
        return 0 if output else 1
    
    # No prompt provided
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
