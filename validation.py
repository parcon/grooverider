# __project__ = "Audio-to-Vinyl STL Generator"
__version__ = "1.5.3"
__author__ = "Gemini AI"
__filename__ = "validation.py"
# __description__ = "Handles validation of the generated STL file against the source audio."

import numpy as np
from stl import mesh
from scipy.spatial import KDTree
from scipy.io.wavfile import write as write_wav
from scipy.signal import resample
import io
import matplotlib.pyplot as plt
import plotly.graph_objects as go

def extract_audio_from_stl(stl_path, config, rpm, progress_bar=None, status_text=None):
    """
    Extracts an audio waveform by finding the lowest point in a search
    cylinder along the spiral path, simulating a stylus.
    """
    if status_text: status_text.info("⚙️ Loading STL file...")
    record_mesh = mesh.Mesh.from_file(stl_path)
    vertices = record_mesh.vectors.reshape(-1, 3)

    if status_text: status_text.info("🌳 Building spatial search tree...")
    tree = KDTree(vertices)

    dims = config['record_dimensions']
    geom = config['groove_geometry']
    
    radius = dims['record_diameter_mm'] / 2.0
    r_start = radius - dims['lead_in_groove_mm']
    r_end = dims['center_hole_diameter_mm'] / 2.0 + 2.0

    seconds_per_rotation = 60.0 / rpm
    total_rotations = (r_start - r_end) / geom['groove_pitch_mm']
    total_duration_seconds = total_rotations * seconds_per_rotation
    
    proxy_sr = 22050 
    num_points = int(total_duration_seconds * proxy_sr)
    theta = np.linspace(0, total_rotations * 2 * np.pi, num=num_points)
    r = np.linspace(r_start, r_end, num=num_points)

    decimation_factor = 20
    indices_to_check = np.arange(0, len(theta), decimation_factor)
    num_steps = len(indices_to_check)
    
    if status_text: status_text.info(f"🔬 Analyzing {num_steps} points on the groove...")

    extracted_depths = []
    base_depth = -geom['groove_depth_mm']
    search_radius = geom['groove_pitch_mm'] / 2.0

    for i, idx in enumerate(indices_to_check):
        angle, radius_val = theta[idx], r[idx]
        x, y = radius_val * np.cos(angle), radius_val * np.sin(angle)
        
        # Find all vertices within a cylinder around the ideal spiral point
        indices_in_radius = tree.query_ball_point([x, y, 0], r=search_radius)
        
        if not indices_in_radius:
            # If no points are found, assume it's a silent part at base depth
            z_val = base_depth
        else:
            # Of the points found, take the one with the lowest Z value
            points_in_cylinder = vertices[indices_in_radius]
            lowest_point = points_in_cylinder[np.argmin(points_in_cylinder[:, 2])]
            z_val = lowest_point[2]

        amplitude = (z_val - base_depth) / (geom['amplitude_scale'] * geom['groove_depth_mm'])
        extracted_depths.append(amplitude)

        if progress_bar:
            progress_bar.progress(i / num_steps)
            
    extracted_samples = np.array(extracted_depths, dtype=np.float32)

    max_abs = np.max(np.abs(extracted_samples))
    if max_abs > 0:
        extracted_samples /= max_abs

    return extracted_samples

def compare_audio_signals(original_samples, extracted_samples):
    """
    Compares two audio signals and generates a plot by resampling
    the shorter signal to match the longer one.
    """
    if len(extracted_samples) == 0 or len(original_samples) == 0:
        return 0.0, plt.figure()

    if len(original_samples) > len(extracted_samples):
        num_samples = len(original_samples)
        extracted_final = resample(extracted_samples, num_samples)
        original_final = original_samples
    else:
        num_samples = len(extracted_samples)
        original_final = resample(original_samples, num_samples)
        extracted_final = extracted_samples
    
    correlation = np.corrcoef(original_final, extracted_final)[0, 1]
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True, sharey=True)
    
    ax1.plot(original_final, label="Original Processed Audio", color='dodgerblue')
    ax1.set_title("Original Processed Audio")
    ax1.set_ylabel("Amplitude")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(extracted_final, label="Audio Extracted from STL", color='darkorange', linestyle='--')
    ax2.set_title("Audio Extracted from STL")
    ax2.set_xlabel("Sample Number")
    ax2.set_ylabel("Amplitude")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    return correlation, fig

def convert_samples_to_wav_bytes(samples, sample_rate):
    """Converts a numpy array of audio samples to WAV file bytes."""
    if len(samples) == 0:
        samples = np.array([0], dtype=np.float32)
        
    samples_int16 = (samples * 32767).astype(np.int16)
    byte_io = io.BytesIO()
    write_wav(byte_io, int(sample_rate), samples_int16)
    return byte_io.getvalue()

def create_3d_figure(stl_path):
    """Creates an interactive 3D plot of the STL mesh using Plotly."""
    m = mesh.Mesh.from_file(stl_path)
    
    vectors = m.vectors
    x, y, z = vectors.reshape(-1, 3).T
    
    i, j, k = np.arange(len(x)).reshape(-1, 3).T

    fig = go.Figure(data=[
        go.Mesh3d(
            x=x, y=y, z=z, 
            i=i, j=j, k=k, 
            color='cyan', 
            opacity=0.9
        )
    ])
    fig.update_layout(
        scene=dict(xaxis_title='X (mm)', yaxis_title='Y (mm)', zaxis_title='Z (mm)', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return fig

def validate_stl(stl_path, original_samples, sample_rate, config, rpm, progress_bar, status_text):
    """Runs the full validation pipeline and returns a dictionary of results."""
    
    extracted_samples = extract_audio_from_stl(stl_path, config, rpm, progress_bar, status_text)
    
    if status_text: status_text.info("📊 Comparing waveforms...")
    score, fig_wave = compare_audio_signals(original_samples, extracted_samples)
    
    if status_text: status_text.info("🔊 Preparing audio playback...")
    original_wav = convert_samples_to_wav_bytes(original_samples, sample_rate)
    
    if len(extracted_samples) > 0:
        resampled_extracted = resample(extracted_samples, len(original_samples))
        extracted_wav = convert_samples_to_wav_bytes(resampled_extracted, sample_rate)
    else:
        extracted_wav = convert_samples_to_wav_bytes(extracted_samples, sample_rate)

    if status_text: status_text.info("🧊 Generating 3D model view...")
    fig_3d = create_3d_figure(stl_path)

    return {
        "similarity_score": score,
        "fig_wave": fig_wave,
        "original_wav": original_wav,
        "extracted_wav": extracted_wav,
        "fig_3d": fig_3d
    }

