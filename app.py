import streamlit as st
import os
from datetime import datetime
import matplotlib.pyplot as plt

# Import project modules
import config
import audio_processing
import geometry_generator
import validation

# --- App Setup ---
st.set_page_config(
    page_title="Audio-to-Vinyl STL Generator",
    page_icon="💿",
    layout="centered"
)

# Initialize session state for generated file paths and data
if 'output_path' not in st.session_state:
    st.session_state.output_path = None
if 'original_samples' not in st.session_state:
    st.session_state.original_samples = None
if 'sample_rate' not in st.session_state:
    st.session_state.sample_rate = None


st.title("💿 Audio-to-Vinyl STL Generator")
st.markdown("Convert your MP3 audio files into 3D-printable vinyl records.")

# --- Load Configuration ---
try:
    # Load config using the imported module
    app_config = config.load_config()
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.stop()

# --- User Interface ---
with st.sidebar:
    st.header("Configuration")
    st.write("Current settings from `config.toml`:")
    st.json(app_config)

st.header("1. Upload Your Audio File")
uploaded_file = st.file_uploader(
    "Choose an MP3 file",
    type=["mp3"],
    help="Only MP3 format is supported."
)

st.header("2. Select Record Style")
rpm_choice = st.radio(
    "Playback Speed (RPM)",
    options=['33⅓ RPM', '45 RPM'],
    horizontal=True
)
rpm_value = 33.33 if '33' in rpm_choice else 45.0

st.header("3. Generate Your Record")
generate_button = st.button(
    "Generate STL File",
    type="primary",
    disabled=(uploaded_file is None)
)

# --- Main Logic ---
if generate_button and uploaded_file is not None:
    temp_dir = "temp"
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    input_path = os.path.join(temp_dir, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    progress_bar = st.progress(0, text="Starting process...")
    status_text = st.empty()

    try:
        status_text.info("Applying Inverse-RIAA Curve & Processing Audio...")
        samples, sample_rate = audio_processing.process_audio(input_path, app_config)
        st.session_state.original_samples = samples
        st.session_state.sample_rate = sample_rate
        progress_bar.progress(33, text="Audio processing complete.")

        status_text.info("Generating Groove Mesh...")
        record_mesh = geometry_generator.create_record_mesh(
            samples, sample_rate, rpm_value, app_config
        )
        progress_bar.progress(66, text="Record mesh created.")

        status_text.info("Saving STL file...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"record_{timestamp}.stl"
        output_path = os.path.join(temp_dir, output_filename)
        record_mesh.save(output_path)
        st.session_state.output_path = output_path
        progress_bar.progress(100, text="Process complete!")

        status_text.success(f"Your record is ready! Click below to download.")
        with open(output_path, "rb") as f:
            st.download_button(
                label=f"Download {output_filename}",
                data=f,
                file_name=output_filename,
                mime="model/stl"
            )

    except Exception as e:
        st.error(f"An error occurred during generation: {e}")
        st.exception(e)
    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

# --- Validation Section ---
if st.session_state.output_path:
    st.header("4. Validate Your Record (Optional)")
    st.markdown("This routine analyzes the STL file to reconstruct the audio waveform. You can listen to both versions and see a visual comparison.")

    validate_button = st.button("Validate Generated STL")

    if validate_button:
        with st.spinner("Validating STL file... This may take a moment."):
            try:
                extracted_samples = validation.extract_audio_from_stl(
                    st.session_state.output_path, app_config, rpm_value
                )

                st.subheader("Auditory Comparison")
                original_wav = validation.convert_samples_to_wav_bytes(
                    st.session_state.original_samples, st.session_state.sample_rate
                )
                st.write("Original Processed Audio:")
                st.audio(original_wav, format='audio/wav')

                extracted_wav = validation.convert_samples_to_wav_bytes(
                    extracted_samples, st.session_state.sample_rate
                )
                st.write("Audio Extracted from STL:")
                st.audio(extracted_wav, format='audio/wav')

                st.subheader("Visual Comparison")
                similarity_score, fig = validation.compare_audio_signals(
                    st.session_state.original_samples, extracted_samples
                )

                st.metric(
                    label="Waveform Similarity (Correlation Score)",
                    value=f"{similarity_score:.4f}"
                )
                st.pyplot(fig)

            except Exception as e:
                st.error(f"An error occurred during validation: {e}")
                st.exception(e)
