# __project__ = "Audio-to-Vinyl STL Generator"
__version__ = "1.2.0"
__author__ = "Gemini AI"
__filename__ = "audio_processing.py"
# __description__ = "Handles the audio processing pipeline: loading, filtering, and effects."

from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, high_pass_filter, low_pass_filter
from scipy.signal import butter, bilinear, lfilter
import numpy as np

def design_riaa_preemphasis(fs):
    """Designs a stable digital RIAA pre-emphasis filter."""
    f1, f2, f3 = 50.05, 500.5, 2122.1
    num_analog = [1 / (2*np.pi*f2), 1]
    den_analog = [1 / (4*np.pi**2*f1*f3), 1/ (2*np.pi*f1) + 1/(2*np.pi*f3), 1]
    b, a = bilinear(num_analog, den_analog, fs=fs)
    return b, a

def process_audio(file_path, config):
    """Full audio processing pipeline."""
    audio_params = config['audio_processing']
    compressor_params = config['compressor']
    padding_params = config['padding_ms']

    # 1. Load audio file
    audio = AudioSegment.from_mp3(file_path)

    # 2. Add silent intro/outro
    lead_in = AudioSegment.silent(duration=padding_params.get('lead_in', 1000))
    lead_out = AudioSegment.silent(duration=padding_params.get('lead_out', 1000))
    audio = lead_in + audio + lead_out

    # 3. Prepare audio: mono, resample, high-pass
    target_sr = audio_params['sample_rate']
    audio = audio.set_channels(1)
    audio = audio.set_frame_rate(target_sr)
    audio = high_pass_filter(audio, cutoff=audio_params['highpass_cutoff_hz'])

    # 4. Convert to numpy array for filtering
    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= (2**(audio.sample_width * 8 - 1))

    # 5. Apply RIAA pre-emphasis filter
    b_riaa, a_riaa = design_riaa_preemphasis(fs=target_sr)
    samples = lfilter(b_riaa, a_riaa, samples)

    # 6. Normalize to prevent clipping
    max_val = np.max(np.abs(samples))
    if max_val > 0:
        samples /= max_val
    
    # 7. Convert back to pydub for compression
    samples_int = (samples * (2**(audio.sample_width * 8 - 1) - 1)).astype(np.int16)
    audio = AudioSegment(
        samples_int.tobytes(),
        frame_rate=target_sr,
        sample_width=audio.sample_width,
        channels=1
    )

    # 8. Apply dynamic range compression
    audio = compress_dynamic_range(audio,
        threshold=compressor_params['threshold_db'],
        ratio=compressor_params['ratio'],
        attack=compressor_params['attack_ms'],
        release=compressor_params['release_ms']
    )

    # 9. Apply low-pass filter (anti-aliasing)
    audio = low_pass_filter(audio, cutoff=audio_params['lowpass_cutoff_hz'])

    # 10. Final conversion and normalization
    final_samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    final_samples /= (2**(audio.sample_width * 8 - 1))

    return final_samples, target_sr
