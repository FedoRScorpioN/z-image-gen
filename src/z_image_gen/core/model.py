"""
Model management - download and verify Z-Image GGUF models
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass

import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn

from z_image_gen.config.paths import get_model_cache_path

console = Console()


@dataclass
class ModelInfo:
    """Model metadata"""
    name: str
    filename: str
    url: str
    size_bytes: int
    sha256: Optional[str] = None


# Z-Image-Turbo model configuration
MODELS = {
    "q4_0": ModelInfo(
        name="Z-Image-Turbo Q4_0",
        filename="z_image_turbo-Q4_0.gguf",
        url="https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q4_0.gguf",
        size_bytes=3_950_000_000,  # ~3.68 GB
    ),
    "q5_0": ModelInfo(
        name="Z-Image-Turbo Q5_0",
        filename="z_image_turbo-Q5_0.gguf",
        url="https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q5_0.gguf",
        size_bytes=4_870_000_000,  # ~4.54 GB
    ),
    "q8_0": ModelInfo(
        name="Z-Image-Turbo Q8_0",
        filename="z_image_turbo-Q8_0.gguf",
        url="https://huggingface.co/leejet/Z-Image-Turbo-GGUF/resolve/main/z_image_turbo-Q8_0.gguf",
        size_bytes=7_060_000_000,  # ~6.58 GB
    ),
}


class ModelManager:
    """Manage model download and caching"""
    
    def __init__(self, model_type: str = "q4_0", cache_dir: Optional[Path] = None):
        """
        Initialize model manager.
        
        Args:
            model_type: Model type (q4_0, q5_0, q8_0)
            cache_dir: Custom cache directory (default: system cache)
        """
        if model_type not in MODELS:
            raise ValueError(f"Unknown model type: {model_type}. Available: {list(MODELS.keys())}")
        
        self.model_type = model_type
        self.model_info = MODELS[model_type]
        self.cache_dir = cache_dir or get_model_cache_path()
        self.model_path = self.cache_dir / self.model_info.filename
    
    def is_downloaded(self) -> bool:
        """Check if model is already downloaded"""
        return self.model_path.exists() and self.model_path.stat().st_size > 0
    
    def get_model_path(self) -> Path:
        """
        Get path to model file, downloading if necessary.
        
        Returns:
            Path to the model file
        """
        if not self.is_downloaded():
            self.download()
        return self.model_path
    
    def download(self, progress_callback: Optional[Callable[[int, int], None]] = None) -> None:
        """
        Download the model with progress display.
        
        Args:
            progress_callback: Optional callback for progress updates (downloaded, total)
        """
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Temporary download path
        temp_path = self.model_path.with_suffix(".downloading")
        
        console.print(f"\n[bold blue]Downloading {self.model_info.name}...[/bold blue]")
        console.print(f"[dim]URL: {self.model_info.url}[/dim]")
        console.print(f"[dim]Size: {self.model_info.size_bytes / (1024**3):.2f} GB[/dim]")
        console.print()
        
        try:
            # Stream download with progress
            response = requests.get(self.model_info.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', self.model_info.size_bytes))
            downloaded = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                DownloadColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeRemainingColumn(),
                console=console,
            ) as progress:
                task = progress.add_task("Downloading", total=total_size)
                
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            progress.update(task, completed=downloaded)
                            
                            if progress_callback:
                                progress_callback(downloaded, total_size)
            
            # Move to final location
            shutil.move(str(temp_path), str(self.model_path))
            
            console.print(f"\n[bold green]✓ Model downloaded successfully![/bold green]")
            console.print(f"[dim]Saved to: {self.model_path}[/dim]")
            
        except requests.RequestException as e:
            # Clean up partial download
            if temp_path.exists():
                temp_path.unlink()
            raise DownloadError(f"Failed to download model: {e}")
        
        except KeyboardInterrupt:
            # Clean up on user interrupt
            if temp_path.exists():
                temp_path.unlink()
            console.print("\n[yellow]Download cancelled.[/yellow]")
            raise
    
    def verify(self) -> bool:
        """
        Verify model integrity (if SHA256 is available).
        
        Returns:
            True if model is valid
        """
        if not self.model_path.exists():
            return False
        
        if self.model_info.sha256 is None:
            # No checksum available, just check file size
            return self.model_path.stat().st_size > 0
        
        console.print("[dim]Verifying model integrity...[/dim]")
        
        sha256_hash = hashlib.sha256()
        with open(self.model_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest() == self.model_info.sha256
    
    def delete(self) -> None:
        """Delete the model from cache"""
        if self.model_path.exists():
            self.model_path.unlink()
            console.print(f"[yellow]Model deleted: {self.model_path}[/yellow]")
    
    @staticmethod
    def list_available_models() -> list:
        """List all available model types"""
        return [
            {
                "type": key,
                "name": info.name,
                "size_gb": info.size_bytes / (1024**3),
                "recommended_vram": "4GB" if key == "q4_0" else "6GB" if key == "q5_0" else "8GB+",
            }
            for key, info in MODELS.items()
        ]


class DownloadError(Exception):
    """Failed to download model"""
    pass


class ModelNotFoundError(Exception):
    """Model file not found"""
    pass
