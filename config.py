# __project__ = "Audio-to-Vinyl STL Generator"
__version__ = "1.2.0"
__author__ = "Gemini AI"
__filename__ = "config.py"
# __description__ = "Loads and validates the application configuration from a TOML file."

import toml

DEFAULT_CONFIG = {
    "audio_processing": {
        "sample_rate": 44100,
        "lowpass_cutoff_hz": 5500,
        "highpass_cutoff_hz": 50,
    },
    "padding_ms": {
        "lead_in": 1000,
        "lead_out": 1000,
    },
    "compressor": {
        "threshold_db": -12.0,
        "ratio": 2.5,
        "attack_ms": 5,
        "release_ms": 100,
    },
    "groove_geometry": {
        "bit_depth": 6,
        "groove_pitch_mm": 0.15,
        "amplitude_scale": 1.0,
        "groove_depth_mm": 0.03
    },
    "record_dimensions": {
        "record_diameter_mm": 177.8,
        "center_hole_diameter_mm": 7.24,
        "record_thickness_mm": 1.5,
        "lead_in_groove_mm": 5.0
    },
    "printer_profile": {
        "name": "Default High-Resolution Resin Printer",
        "layer_height_mm": 0.025,
    }
}

def load_config(path="config.toml"):
    """
    Loads the configuration from a TOML file.
    If the file doesn't exist, it returns the default configuration.
    """
    try:
        with open(path, "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        return DEFAULT_CONFIG

