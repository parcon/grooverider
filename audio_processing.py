# Groove Rider
# Copyright (c) 2024
#
# This script handles the audio processing pipeline for Groove Rider. It is
# responsible for loading an audio file, converting it to a suitable format,
# and extracting the raw sample data needed for geometry generation.

import numpy as np
from pydub import AudioSegment
import io
from config import AppConfig

def load_and_process_audio(file_path: str, cfg: AppConfig) -> np.ndarray:
    """
    Loads an audio file, converts it to mono, and normalizes the waveform.
    Includes a downsampling step to reduce the final STL file size.
    
    Args:
        file_path: The path to the audio file.
        cfg: The application configuration object.

    Returns:
        A NumPy array of the audio samples.
    """
    # Load audio file from file-like object
    audio = AudioSegment.from_file(io.BytesIO(file_path.read()), format=file_path.name.split('.')[-1])

    # Convert to mono
    audio = audio.set_channels(1)

    # Downsample the audio to reduce the number of vertices in the final mesh
    target_samplerate = cfg.audio.get('target_samplerate', 8000)
    audio = audio.set_frame_rate(target_samplerate)

    # Get raw audio data as a NumPy array
    samples = np.array(audio.get_array_of_samples())

    # Normalize samples to be between -1 and 1
    samples = samples / np.max(np.abs(samples))

    return samples

