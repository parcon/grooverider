# Groove Rider
# Copyright (c) 2024
#
# This script handles loading and accessing application configuration
# from the config.toml file.

import toml
from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class AppConfig:
    """
    A dataclass to hold the application's configuration settings,
    loaded from a TOML file.
    """
    record: Dict[str, Any] = field(default_factory=dict)
    audio: Dict[str, Any] = field(default_factory=dict)
    server: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """
        Loads the configuration from the TOML file after the
        object has been initialized.
        """
        self._load_config()

    def _load_config(self, path: str = "config.toml"):
        """
        Private method to parse the TOML file and populate the
        dataclass fields.
        """
        try:
            with open(path, "r") as f:
                config_data = toml.load(f)
                self.record = config_data.get('record', self.record)
                self.audio = config_data.get('audio', self.audio)
                self.server = config_data.get('server', self.server)
        except FileNotFoundError:
            # It's good practice to handle the case where the config file is missing
            print(f"Warning: Configuration file '{path}' not found. Using default values.")
        except Exception as e:
            # Catch other potential errors during file loading
            print(f"Error loading configuration from '{path}': {e}")
