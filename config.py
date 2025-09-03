import toml
from typing import Dict, Any

DEFAULT_CONFIG = {
    "audio_processing": {
        "lowpass_cutoff_hz": 5500,
        "compressor_threshold_db": -12.0,
        "compressor_ratio": 2.5,
        "sample_rate": 44100
    },
    "groove_geometry": {
        "groove_pitch_mm": 0.158,
        "groove_top_width_mm": 0.06,
        "groove_depth_mm": 0.025,
        "amplitude_scale": 1.0
    },
    "record_dimensions": {
        "record_diameter_mm": 177.8,
        "center_hole_diameter_mm": 7.24,
        "record_thickness_mm": 1.5,
        "lead_in_groove_mm": 5.0
    },
    "printer_profile": {
        "name": "Default High-Resolution Resin Printer",
        "layer_height_mm": 0.025
    }
}

def load_config(path: str = "config.toml") -> Dict[str, Any]:
    """
    Loads configuration from a TOML file.

    If the file is not found, it returns a default configuration dictionary.

    Args:
        path (str): The path to the configuration file.

    Returns:
        A dictionary containing the configuration parameters.
    """
    try:
        with open(path, "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        print(f"Warning: '{path}' not found. Using default configuration.")
        return DEFAULT_CONFIG
