import numpy as np
from pydub import AudioSegment
from scipy.signal import butter, lfilter

def apply_inverse_riaa(samples, fs):
    """
    Applies an inverse RIAA pre-emphasis filter to the audio samples.
    """
    t1 = 75e-6
    t2 = 318e-6
    t3 = 3180e-6
    num = [1, 0, -np.exp(-1/(t1*fs))]
    den = [1, -np.exp(-1/(t2*fs)) - np.exp(-1/(t3*fs)), np.exp(-(1/(t2*fs) + 1/(t3*fs)))]
    return lfilter(num, den, samples)

def apply_lowpass_filter(samples, cutoff_hz, fs):
    """
    Applies a steep low-pass filter.
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_hz / nyquist
    b, a = butter(8, normal_cutoff, btype='low', analog=False)
    return lfilter(b, a, samples)

def apply_compressor(samples, threshold_db, ratio):
    """
    Applies a simple dynamic range compressor.
    """
    threshold = 10**(threshold_db/20)
    compressed_samples = np.copy(samples)
    over_threshold_indices = np.abs(samples) > threshold
    compressed_samples[over_threshold_indices] = (
        np.sign(samples[over_threshold_indices]) * (threshold + (np.abs(samples[over_threshold_indices]) - threshold) / ratio)
    )
    return compressed_samples

def process_audio(file_path: str, config: dict):
    """
    Loads an MP3 file and runs it through the full audio processing pipeline.
    """
    audio = AudioSegment.from_mp3(file_path)
    audio = audio.set_channels(1)

    target_sr = config['audio_processing']['sample_rate']
    audio = audio.set_frame_rate(target_sr)

    samples = np.array(audio.get_array_of_samples()).astype(np.float32)
    samples /= (2**(audio.sample_width * 8 - 1))

    samples = apply_inverse_riaa(samples, target_sr)
    samples = apply_compressor(
        samples,
        config['audio_processing']['compressor_threshold_db'],
        config['audio_processing']['compressor_ratio']
    )
    samples = apply_lowpass_filter(
        samples,
        config['audio_processing']['lowpass_cutoff_hz'],
        target_sr
    )

    samples /= np.max(np.abs(samples))
    return samples, target_sr
