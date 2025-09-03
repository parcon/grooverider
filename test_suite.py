import pytest
import numpy as np
import os
from pydub import AudioSegment
from stl import mesh

# Import the project modules to be tested
import config
import audio_processing
import geometry_generator
import validation

# --- Fixtures ---

@pytest.fixture(scope="module")
def test_config():
    """Provides a standard configuration for all tests."""
    return config.DEFAULT_CONFIG

@pytest.fixture(scope="module")
def test_audio_file(tmpdir_factory):
    """Creates a temporary sine wave audio file for testing."""
    sample_rate = 44100
    t = np.linspace(0., 2, int(sample_rate * 2), endpoint=False)
    amplitude = np.iinfo(np.int16).max * 0.5
    data = (amplitude * np.sin(2. * np.pi * 440 * t)).astype(np.int16)

    audio_segment = AudioSegment(data.tobytes(), frame_rate=sample_rate, sample_width=2, channels=1)

    file_path = tmpdir_factory.mktemp("audio").join("test_sine.mp3")
    audio_segment.export(str(file_path), format="mp3")
    return str(file_path)

# --- Tests ---

def test_config_loading():
    """Tests that the config loader returns defaults when a file is not found."""
    loaded_config = config.load_config("non_existent_file.toml")
    assert loaded_config == config.DEFAULT_CONFIG

def test_audio_processing_pipeline(test_audio_file, test_config):
    """Tests the full audio processing pipeline."""
    samples, sample_rate = audio_processing.process_audio(test_audio_file, test_config)
    assert isinstance(samples, np.ndarray)
    assert len(samples) > 0
    assert np.max(np.abs(samples)) <= 1.0
    assert sample_rate == test_config['audio_processing']['sample_rate']

def test_geometry_generation(test_config):
    """Tests the mesh generation function."""
    sample_rate = 44100
    test_samples = np.sin(np.linspace(0, 2 * np.pi * 440, sample_rate))

    record_mesh = geometry_generator.create_record_mesh(test_samples, sample_rate, 45.0, test_config)

    assert isinstance(record_mesh, mesh.Mesh)
    assert record_mesh.vectors.shape[0] > 0
    assert record_mesh.points.shape[0] > 0

def test_full_integration_and_validation(test_config, tmpdir):
    """An end-to-end test that generates and validates a record."""
    sample_rate = test_config['audio_processing']['sample_rate']
    original_samples = np.sin(2. * np.pi * 500 * np.linspace(0., 1, sample_rate))

    record_mesh = geometry_generator.create_record_mesh(original_samples, sample_rate, 33.33, test_config)

    stl_path = tmpdir.join("validation_test.stl")
    record_mesh.save(str(stl_path))

    extracted_samples = validation.extract_audio_from_stl(str(stl_path), test_config, 33.33)

    correlation, _ = validation.compare_audio_signals(original_samples, extracted_samples)

    assert correlation > 0.90
