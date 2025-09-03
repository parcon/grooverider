# __project__ = "Audio-to-Vinyl STL Generator"
# __version__ = "1.1.0"
# __author__ = "Gemini AI"
# __filename__ = "config.py"
# __description__ = "Handles loading the TOML configuration file."

import toml

DEFAULT_CONFIG = {
    "audio_processing": {
        "sample_rate": 44100,
        "lowpass_cutoff_hz": 12000,
        "compressor_threshold_db": -10.0,
        "compressor_ratio": 2.0,
    },
    "groove_geometry": {
        "groove_pitch_mm": 0.15,
        "groove_depth_mm": 0.06,
        "amplitude_scale": 0.8,
    },
    "record_dimensions": {
        "record_diameter_mm": 177.8,
        "center_hole_diameter_mm": 7.24,
        "record_thickness_mm": 1.6,
        "lead_in_groove_mm": 5.0,
    },
}

def load_config(path="config.toml"):
    """
    Loads configuration from a TOML file.
    If the file doesn't exist, it returns the default configuration.
    """
    try:
        with open(path, "r") as f:
            return toml.load(f)
    except FileNotFoundError:
        return DEFAULT_CONFIG


