"""Tests for configuration module"""

import pytest
from pathlib import Path

from z_image_gen.config.settings import Settings
from z_image_gen.config.paths import get_downloads_folder, get_model_cache_path


class TestSettings:
    """Test Settings class"""
    
    def test_default_settings(self):
        """Test default settings creation"""
        settings = Settings()
        
        assert settings.model_type == "q4_0"
        assert settings.width == 768
        assert settings.height == 512
        assert settings.steps == 4
        assert settings.low_vram_mode == True
        assert settings.vae_on_cpu == True
    
    def test_custom_settings(self):
        """Test custom settings"""
        settings = Settings(
            model_type="q8_0",
            width=1024,
            height=576,
            steps=8,
        )
        
        assert settings.model_type == "q8_0"
        assert settings.width == 1024
        assert settings.height == 576
        assert settings.steps == 8
    
    def test_output_dir_resolution(self):
        """Test output directory resolution"""
        settings = Settings()
        
        assert settings.output_dir is not None
        assert isinstance(settings.output_dir, Path)
    
    def test_get_output_path(self):
        """Test output path generation"""
        settings = Settings()
        
        path = settings.get_output_path(seed=42)
        
        assert isinstance(path, Path)
        assert "zimage_42_" in path.name
        assert path.suffix == ".png"
    
    def test_from_env(self, monkeypatch):
        """Test settings from environment variables"""
        monkeypatch.setenv("Z_IMAGE_WIDTH", "1024")
        monkeypatch.setenv("Z_IMAGE_HEIGHT", "576")
        monkeypatch.setenv("Z_IMAGE_STEPS", "8")
        
        settings = Settings.from_env()
        
        assert settings.width == 1024
        assert settings.height == 576
        assert settings.steps == 8


class TestPaths:
    """Test path resolution"""
    
    def test_get_downloads_folder(self):
        """Test downloads folder resolution"""
        path = get_downloads_folder()
        
        assert isinstance(path, Path)
        assert path.exists() or path.parent.exists()  # May not exist yet
    
    def test_get_model_cache_path(self):
        """Test model cache path resolution"""
        path = get_model_cache_path()
        
        assert isinstance(path, Path)
        assert "z-image-gen" in str(path).lower() or "models" in str(path).lower()
