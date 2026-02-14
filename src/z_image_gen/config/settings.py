"""
Configuration management for z-image-gen
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from z_image_gen.config.paths import get_downloads_folder, get_config_path


@dataclass
class Settings:
    """Application settings with defaults optimized for 4GB VRAM"""
    
    # Model settings
    model_type: str = "q4_0"
    auto_download: bool = True
    
    # Generation settings (optimized for Z-Image-Turbo)
    width: int = 768
    height: int = 512
    steps: int = 4  # Turbo model uses 4 steps
    guidance_scale: float = 0.0  # Turbo doesn't need guidance
    sample_method: str = "euler_a"
    scheduler: str = "discrete"
    
    # Output settings
    output_dir: Optional[Path] = None
    filename_template: str = "zimage_{seed}_{timestamp}"
    save_metadata: bool = True
    
    # Performance settings (optimized for 4GB VRAM)
    use_cuda: bool = True
    low_vram_mode: bool = True
    vae_on_cpu: bool = True
    clip_on_cpu: bool = False
    
    # Display settings
    verbose: bool = False
    show_progress: bool = True
    
    def __post_init__(self):
        """Resolve paths after initialization"""
        if self.output_dir is None:
            self.output_dir = get_downloads_folder()
        
        # Ensure output directory exists
        if isinstance(self.output_dir, Path):
            self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables"""
        return cls(
            model_type=os.getenv("Z_IMAGE_MODEL_TYPE", "q4_0"),
            width=int(os.getenv("Z_IMAGE_WIDTH", "768")),
            height=int(os.getenv("Z_IMAGE_HEIGHT", "512")),
            steps=int(os.getenv("Z_IMAGE_STEPS", "4")),
            output_dir=Path(path) if (path := os.getenv("Z_IMAGE_OUTPUT_DIR")) else None,
            low_vram_mode=os.getenv("Z_IMAGE_LOW_VRAM", "true").lower() == "true",
            use_cuda=os.getenv("Z_IMAGE_CUDA", "true").lower() == "true",
            verbose=os.getenv("Z_IMAGE_VERBOSE", "false").lower() == "true",
        )
    
    def get_output_path(self, seed: int = -1, timestamp: str = None) -> Path:
        """Generate output file path"""
        import datetime
        
        if timestamp is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filename = self.filename_template.format(
            seed=seed if seed >= 0 else "random",
            timestamp=timestamp,
        )
        
        return self.output_dir / f"{filename}.png"


# Default settings instance
DEFAULT_SETTINGS = Settings()
