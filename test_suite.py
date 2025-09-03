# __project__ = "Audio-to-Vinyl STL Generator"
# __version__ = "1.1.0"
# __author__ = "Gemini AI"
# __filename__ = "test_suite.py"
# __description__ = "Test suite for the application using pytest."

import os
import numpy as np
from pydub import AudioSegment
import pytest

# Import project modules to be tested
import config
import audio_processing
import geometry_generator
import validation

# --- Test Fixtures ---
@pytest.fixture(scope="module")
def app_config():
    """Provides a default configuration for tests."""
    return config.load_config()

@pytest.fixture(scope="module")
def silent_mp3_file(tmpdir_factory):
    """Creates a short, silent MP3 file for testing purposes."""
    # Create a 1-second silent audio segment
    silent_audio = AudioSegment.silent(duration=1000, frame_rate=44100)
    
    # Export to a temporary file
    fn = tmpdir_factory.mktemp("data").join("silent.mp3")
    silent_audio.export(str(fn), format="mp3")
    return str(fn)

# --- Unit Tests ---
def test_config_loading():
    """Tests that the configuration loader returns a dictionary."""
    cfg = config.load_config()
    assert isinstance(cfg, dict)
    assert "audio_processing" in cfg

def test_audio_processing(silent_mp3_file, app_config):
    """Tests that audio processing returns a valid numpy array and sample rate."""
    samples, sample_rate = audio_processing.process_audio(silent_mp3_file, app_config)
    assert isinstance(samples, np.ndarray)
    assert isinstance(sample_rate, int)
    assert sample_rate == app_config['audio_processing']['sample_rate']
    assert len(samples) > 0

# --- Integration Test ---
def test_full_generation_and_validation(silent_mp3_file, app_config):
    """
    An end-to-end test that generates an STL from an audio file and then
    validates the output.
    """
    # 1. Process audio
    samples, rate = audio_processing.process_audio(silent_mp3_file, app_config)
    
    # 2. Generate mesh
    record_mesh = geometry_generator.create_record_mesh(samples, rate, 33.33, app_config)
    
    # 3. Save STL to a temporary location
    temp_stl_path = "temp_test_record.stl"
    record_mesh.save(temp_stl_path)
    assert os.path.exists(temp_stl_path)
    
    # 4. Validate the STL
    extracted_samples = validation.extract_audio_from_stl(temp_stl_path, app_config, 33.33)
    assert isinstance(extracted_samples, np.ndarray)
    assert len(extracted_samples) > 0

    score, fig = validation.compare_audio_signals(samples, extracted_samples)
    assert isinstance(score, float)
    assert -1.0 <= score <= 1.0

    # Clean up the temporary file
    os.remove(temp_stl_path)

