"""
Image generation engine using stable-diffusion-cpp-python
"""

import gc
import time
from pathlib import Path
from typing import Optional, List, Union

from PIL import Image
from rich.console import Console

from z_image_gen.core.model import ModelManager, ModelNotFoundError
from z_image_gen.config.settings import Settings

console = Console()

# Try to import stable_diffusion_cpp
try:
    from stable_diffusion_cpp import StableDiffusion
    SD_CPP_AVAILABLE = True
except ImportError:
    SD_CPP_AVAILABLE = False
    console.print("[yellow]Warning: stable-diffusion-cpp-python not installed.[/yellow]")
    console.print("[dim]Install with: pip install stable-diffusion-cpp-python[/dim]")


class ZImageGenerator:
    """
    Main generator class for Z-Image text-to-image generation.
    Optimized for low VRAM systems (4GB).
    """
    
    def __init__(
        self,
        model_type: str = "q4_0",
        model_path: Optional[Path] = None,
        settings: Optional[Settings] = None,
    ):
        """
        Initialize the image generator.
        
        Args:
            model_type: Model quantization type (q4_0, q5_0, q8_0)
            model_path: Direct path to model file (overrides model_type)
            settings: Custom settings (uses defaults if None)
        """
        if not SD_CPP_AVAILABLE:
            raise ImportError(
                "stable-diffusion-cpp-python is required. "
                "Install with: pip install stable-diffusion-cpp-python"
            )
        
        self.settings = settings or Settings()
        self.model_type = model_type
        self._sd = None
        self._model_loaded = False
        
        # Determine model path
        if model_path:
            self.model_path = Path(model_path)
            if not self.model_path.exists():
                raise ModelNotFoundError(f"Model not found: {model_path}")
        else:
            manager = ModelManager(model_type)
            self.model_path = manager.get_model_path()
    
    def _load_model(self) -> None:
        """Load the model with VRAM optimizations"""
        if self._model_loaded:
            return
        
        console.print(f"[bold blue]Loading model from {self.model_path}...[/bold blue]")
        
        start_time = time.time()
        
        # Configure for low VRAM
        self._sd = StableDiffusion(
            model_path=str(self.model_path),
            
            # VRAM optimizations for 4GB
            offload_params_to_cpu=self.settings.low_vram_mode,
            flash_attn=True,
            diffusion_flash_attn=True,
            
            # Offload components to save VRAM
            keep_clip_on_cpu=self.settings.clip_on_cpu,
            keep_vae_on_cpu=self.settings.vae_on_cpu,
            vae_decode_only=True,
            
            # Threading
            n_threads=-1,  # Auto-detect
            
            verbose=self.settings.verbose,
        )
        
        load_time = time.time() - start_time
        console.print(f"[green]✓ Model loaded in {load_time:.1f}s[/green]")
        
        self._model_loaded = True
    
    def generate(
        self,
        prompt: str,
        negative_prompt: str = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        steps: Optional[int] = None,
        seed: int = -1,
        cfg_scale: float = 0.0,  # Turbo models don't need guidance
        sample_method: str = "euler_a",
        scheduler: str = "discrete",
    ) -> Image.Image:
        """
        Generate a single image from a text prompt.
        
        Args:
            prompt: Text description of the desired image
            negative_prompt: Things to avoid in the image
            width: Image width (default from settings: 768)
            height: Image height (default from settings: 512)
            steps: Number of sampling steps (default: 4 for Turbo)
            seed: Random seed (-1 for random)
            cfg_scale: Classifier-free guidance scale
            sample_method: Sampling method (euler_a, euler, dpmpp2m, etc.)
            scheduler: Noise scheduler (discrete, karras, etc.)
        
        Returns:
            PIL Image object
        """
        # Load model if needed
        self._load_model()
        
        # Use settings defaults
        width = width or self.settings.width
        height = height or self.settings.height
        steps = steps or self.settings.steps
        
        # Validate dimensions for 4GB VRAM
        if self.settings.low_vram_mode:
            max_pixels = 768 * 512  # ~393k pixels
            current_pixels = width * height
            if current_pixels > max_pixels * 1.1:  # 10% tolerance
                scale = (max_pixels / current_pixels) ** 0.5
                width = int(width * scale)
                height = int(height * scale)
                console.print(f"[yellow]Resolution adjusted to {width}x{height} for VRAM constraints[/yellow]")
        
        console.print(f"\n[bold]Generating image...[/bold]")
        console.print(f"[dim]Prompt: {prompt}[/dim]")
        console.print(f"[dim]Size: {width}x{height} | Steps: {steps} | Seed: {seed}[/dim]")
        
        start_time = time.time()
        
        try:
            images = self._sd.generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                sample_steps=steps,
                seed=seed,
                cfg_scale=cfg_scale,
                sample_method=sample_method,
                scheduler=scheduler,
                batch_count=1,
                
                # VRAM optimization
                vae_tiling=self.settings.low_vram_mode,
            )
            
            generation_time = time.time() - start_time
            console.print(f"[green]✓ Generated in {generation_time:.1f}s[/green]")
            
            # Clean up if needed
            if self.settings.low_vram_mode:
                gc.collect()
            
            return images[0] if images else None
            
        except Exception as e:
            console.print(f"[red]Generation failed: {e}[/red]")
            raise GenerationError(f"Image generation failed: {e}")
    
    def generate_batch(
        self,
        prompts: List[str],
        **kwargs
    ) -> List[Image.Image]:
        """
        Generate multiple images from a list of prompts.
        
        Args:
            prompts: List of text prompts
            **kwargs: Additional generation parameters
        
        Returns:
            List of PIL Image objects
        """
        images = []
        for i, prompt in enumerate(prompts, 1):
            console.print(f"\n[cyan]Image {i}/{len(prompts)}[/cyan]")
            image = self.generate(prompt, **kwargs)
            images.append(image)
        return images
    
    def unload_model(self) -> None:
        """Unload the model from memory"""
        if self._sd is not None:
            del self._sd
            self._sd = None
            self._model_loaded = False
            gc.collect()
            console.print("[dim]Model unloaded from memory[/dim]")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup"""
        self.unload_model()


class GenerationError(Exception):
    """Image generation failed"""
    pass
