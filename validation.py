import numpy as np
from stl import mesh
from scipy.spatial import KDTree
import matplotlib.pyplot as plt
from scipy.io.wavfile import write as write_wav
from io import BytesIO

def convert_samples_to_wav_bytes(samples, sample_rate):
    """
    Converts a numpy array of audio samples to a WAV file in memory.
    """
    int_samples = (samples * 32767).astype(np.int16)
    wav_bytes = BytesIO()
    write_wav(wav_bytes, sample_rate, int_samples)
    wav_bytes.seek(0)
    return wav_bytes

def extract_audio_from_stl(stl_path: str, config: dict, rpm: float):
    """
    Extracts an audio signal by analyzing the groove depth of a record STL file.
    """
    record_mesh = mesh.Mesh.from_file(stl_path)
    vertices = np.unique(record_mesh.vectors.reshape(-1, 3), axis=0)
    kdtree = KDTree(vertices[:, :2])

    dims = config['record_dimensions']
    geom = config['groove_geometry']

    radius = dims['record_diameter_mm'] / 2.0
    center_hole_radius = dims['center_hole_diameter_mm'] / 2.0
    pitch = geom['groove_pitch_mm']

    num_rotations = (radius - dims['lead_in_groove_mm'] - (center_hole_radius + 5)) / pitch

    r_start = radius - dims['lead_in_groove_mm']
    r_end = center_hole_radius + 5

    theta_max = (r_start - r_end) * 2 * np.pi / pitch
    num_points = int(2000 * num_rotations)
    theta = np.linspace(0, theta_max, num_points)

    r = r_start - (pitch * theta / (2 * np.pi))
    x_spiral, y_spiral = r * np.cos(theta), r * np.sin(theta)
    spiral_path = np.vstack([x_spiral, y_spiral]).T

    indices = kdtree.query_ball_point(spiral_path, r=pitch)
    extracted_z = []
    for point_indices in indices:
        if not point_indices:
            extracted_z.append(0)
            continue
        local_vertices = vertices[point_indices]
        min_z_vertex = local_vertices[np.argmin(local_vertices[:, 2])]
        extracted_z.append(min_z_vertex[2])

    extracted_z = np.array(extracted_z)

    base_depth = -geom['groove_depth_mm']
    modulation_range = geom['groove_depth_mm'] * geom['amplitude_scale']

    if modulation_range == 0: return np.zeros_like(extracted_z)
    unscaled_samples = (extracted_z - base_depth) / modulation_range
    return np.clip(unscaled_samples, -1.0, 1.0)

def compare_audio_signals(original_samples, extracted_samples):
    """
    Compares two audio signals by calculating their correlation and plotting them.
    """
    len_orig, len_ext = len(original_samples), len(extracted_samples)
    if len_orig > len_ext:
        resampled_extracted = np.interp(np.linspace(0, len_ext, len_orig), np.arange(len_ext), extracted_samples)
        resampled_original = original_samples
    else:
        resampled_original = np.interp(np.linspace(0, len_orig, len_ext), np.arange(len_orig), original_samples)
        resampled_extracted = extracted_samples

    correlation = np.corrcoef(resampled_original, resampled_extracted)[0, 1]

    fig, ax = plt.subplots(figsize=(12, 6))
    plot_length = min(len(resampled_original), 4000)
    time_axis = np.arange(plot_length)
    ax.plot(time_axis, resampled_original[:plot_length], label="Original Processed Audio", alpha=0.8)
    ax.plot(time_axis, resampled_extracted[:plot_length], label="Audio Extracted from STL", alpha=0.8, linestyle='--')
    ax.set_title("Waveform Comparison (Original vs. Extracted from STL)")
    ax.set_xlabel("Sample Number")
    ax.set_ylabel("Amplitude")
    ax.legend()
    ax.grid(True, linestyle=':', alpha=0.6)

    return correlation, fig
