"""
Cross-platform path resolution for z-image-gen
"""

import os
import sys
from pathlib import Path

from platformdirs import user_cache_dir, user_config_dir, user_downloads_dir


APP_NAME = "z-image-gen"
APP_AUTHOR = "FedoRScorpioN"


def get_downloads_folder() -> Path:
    """
    Get the Windows Downloads folder path.
    
    Returns:
        Path to Downloads folder
    """
    # Try platformdirs first
    try:
        downloads = user_downloads_dir()
        if downloads and Path(downloads).exists():
            return Path(downloads)
    except Exception:
        pass
    
    # Fallback: Try Windows known folders
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes
            
            # GUID for Downloads folder
            FOLDERID_Downloads = "{374DE290-123F-4565-9164-2C9AA0BAD945}"
            
            # Get known folder path
            ctypes.windll.ole32.CoInitialize(None)
            
            # SHGetKnownFolderPath
            SHGetKnownFolderPath = ctypes.windll.shell32.SHGetKnownFolderPath
            SHGetKnownFolderPath.argtypes = [
                ctypes.c_char_p,  # rfid
                wintypes.DWORD,   # dwFlags
                wintypes.HANDLE,  # hToken
                ctypes.POINTER(ctypes.c_wchar_p)  # ppszPath
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
    
    # Final fallback: User profile Downloads
    home = Path.home()
    downloads = home / "Downloads"
    if downloads.exists():
        return downloads
    
    # Last resort: home directory
    return home


def get_model_cache_path() -> Path:
    """
    Get the path for caching model files.
    
    Returns:
        Path to model cache directory
    """
    cache_dir = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    models_dir = cache_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def get_config_path() -> Path:
    """
    Get the path for configuration files.
    
    Returns:
        Path to config directory
    """
    config_dir = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_file() -> Path:
    """
    Get the path to the config file.
    
    Returns:
        Path to config.yaml
    """
    return get_config_path() / "config.yaml"


def ensure_directories() -> None:
    """Ensure all required directories exist"""
    get_model_cache_path()
    get_config_path()
    downloads = get_downloads_folder()
    if not downloads.exists():
        downloads.mkdir(parents=True, exist_ok=True)
