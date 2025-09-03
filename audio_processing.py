# __project__ = "Audio-to-Vinyl STL Generator"
# __version__ = "1.1.0"
# __author__ = "Gemini AI"
# __filename__ = "audio_processing.py"
# __description__ = "Handles the audio processing pipeline using robust digital filters."

import numpy as np
from pydub import AudioSegment
from scipy.signal import butter, sosfilt

def apply_filter(samples, sos, gain=1.0):
    """Applies a second-order sections (SOS) filter to samples."""
    return sosfilt(sos, samples) * gain

def design_riaa_preemphasis(fs):
    """
    Designs a stable digital inverse RIAA pre-emphasis filter using the bilinear transform.
    Returns the filter as second-order sections (SOS) for numerical stability.
    """
    # RIAA time constants in seconds
    t1 = 75e-6
    t2 = 318e-6
    t3 = 3180e-6

    # Analog poles and zeros for the pre-emphasis curve
    z1 = -1 / t1
    z2 = -1 / t3
    p1 = -1 / t2

    # Analog transfer function coefficients
    num_analog = np.convolve([1, -z1], [1, -z2])
    den_analog = [1, -p1, 0]

    # Use a gain factor to normalize the filter's response at 1kHz
    # This prevents the filter from excessively boosting the signal
    w_1k = 2 * np.pi * 1000
    h_1k = np.polyval(num_analog, 1j*w_1k) / np.polyval(den_analog, 1j*w_1k)
    gain = 1.0 / np.abs(h_1k)

    # Convert to digital filter using the bilinear transform
    # output='sos' is crucial for numerical stability
    sos = butter(2, [abs(z1), abs(z2)], btype='bandpass', analog=True, output='sos', fs=fs)
    return sos, gain

def process_audio(file_path: str, config: dict):
    """
    Loads and processes an MP3 file with a robust and stable pipeline.
    """
    cfg = config['audio_processing']
    target_sr = cfg['sample_rate']

    # 1. Load, convert to mono, and resample
    audio = AudioSegment.from_mp3(file_path).set_channels(1).set_frame_rate(target_sr)
    samples = np.array(audio.get_array_of_samples()).astype(np.float32) / (2**(audio.sample_width * 8 - 1))

    # 2. Design the stable RIAA filter
    riaa_sos, riaa_gain = design_riaa_preemphasis(fs=target_sr)

    # 3. Apply low-pass filter to prevent aliasing and remove ultrasonic frequencies
    lp_sos = butter(8, cfg['lowpass_cutoff_hz'], btype='low', fs=target_sr, output='sos')
    samples = apply_filter(samples, lp_sos)

    # 4. Apply the stable inverse RIAA curve
    samples = apply_filter(samples, riaa_sos, gain=riaa_gain)

    # 5. Apply dynamic range compression
    threshold = 10**(cfg['compressor_threshold_db'] / 20.0)
    ratio = cfg['compressor_ratio']
    mask = np.abs(samples) > threshold
    samples[mask] = np.sign(samples[mask]) * (threshold + (np.abs(samples[mask]) - threshold) / ratio)

    # 6. Final normalization to ensure the signal utilizes the full [-1, 1] range
    max_abs = np.max(np.abs(samples))
    if max_abs > 0:
        samples /= max_abs

    return samples, target_sr



