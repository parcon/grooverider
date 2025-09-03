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
    
    r_start = radius - dims['lead_in_groove_mm']
    r_end = center_hole_radius + 5 # Inner radius limit
    
    recordable_width = r_start - r_end
    num_rotations = recordable_width / pitch
    
    theta_max = num_rotations * 2 * np.pi
    
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
    Compares two audio signals by calculating their correlation and plotting them
    on separate subplots.
    """
    len_orig, len_ext = len(original_samples), len(extracted_samples)
    if len_orig == 0 or len_ext == 0:
        return 0.0, plt.figure()

    # Resample the shorter signal to match the length of the longer one
    if len_orig > len_ext:
        resampled_extracted = np.interp(np.linspace(0, len_ext, len_orig, endpoint=False), np.arange(len_ext), extracted_samples)
        resampled_original = original_samples
    else:
        resampled_original = np.interp(np.linspace(0, len_orig, len_ext, endpoint=False), np.arange(len_orig), original_samples)
        resampled_extracted = extracted_samples

    correlation = np.corrcoef(resampled_original, resampled_extracted)[0, 1]

    # Create two subplots, sharing the x-axis
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    plot_length = min(len(resampled_original), 4000)
    time_axis = np.arange(plot_length)
    
    # Plot Original Audio
    ax1.plot(time_axis, resampled_original[:plot_length], label="Original Processed Audio", color='tab:blue')
    ax1.set_title("Original Processed Audio")
    ax1.set_ylabel("Amplitude")
    ax1.legend(loc="upper right")
    ax1.grid(True, linestyle=':', alpha=0.6)
    
    # Plot Extracted Audio
    ax2.plot(time_axis, resampled_extracted[:plot_length], label="Audio Extracted from STL", color='tab:orange', linestyle='--')
    ax2.set_title("Audio Extracted from STL")
    ax2.set_xlabel("Sample Number")
    ax2.set_ylabel("Amplitude")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=':', alpha=0.6)

    fig.tight_layout() # Adjust layout to prevent titles from overlapping
    
    return correlation, fig

def plot_stl_top_down_view(stl_path: str):
    """
    Creates a top-down 2D scatter plot of an STL file's vertices
    to visualize the record's grooves.
    """
    record_mesh = mesh.Mesh.from_file(stl_path)
    # Flatten the vectors to get a list of all vertices
    vertices = record_mesh.vectors.reshape(-1, 3)
    
    fig, ax = plt.subplots(figsize=(8, 8))
    # Create a scatter plot of the X and Y coordinates
    ax.scatter(vertices[:, 0], vertices[:, 1], s=0.01, alpha=0.5, color='black')
    ax.set_aspect('equal', 'box')
    ax.set_title("Top-Down View of STL Grooves")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.set_facecolor('#F0F2F6') # Match Streamlit's light theme background
    
    return fig

