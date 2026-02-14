"""
Z-Image Generator - Local AI image generation optimized for 4GB VRAM

A simple CLI tool for generating images using the Z-Image-Turbo model
with stable-diffusion.cpp backend.
"""

__version__ = "1.0.0"
__author__ = "FedoRScorpioN"

from z_image_gen.core.generator import ZImageGenerator
from z_image_gen.core.model import ModelManager

__all__ = ["ZImageGenerator", "ModelManager", "__version__"]
