# __project__ = "Audio-to-Vinyl STL Generator"
__version__ = "1.1.0"
__author__ = "Gemini AI"
__filename__ = "app.py"
# __description__ = "Main Streamlit application file for the user interface."

import streamlit as st
import os
from datetime import datetime
import audio_processing
import config
import geometry_generator
import validation

# --- App Setup ---
st.set_page_config(
    page_title="Audio-to-Vinyl STL Generator",
    page_icon="💿",
    layout="wide"
)

# --- Session State Initialization ---
if 'output_path' not in st.session_state:
    st.session_state.output_path = None
if 'original_samples' not in st.session_state:
    st.session_state.original_samples = None
if 'sample_rate' not in st.session_state:
    st.session_state.sample_rate = None
if 'validation_results' not in st.session_state:
    st.session_state.validation_results = None

# --- Main UI ---
st.title("💿 Audio-to-Vinyl STL Generator")
st.caption(f"Version {__version__}")

# --- Load Configuration ---
try:
    app_config = config.load_config()
except Exception as e:
    st.error(f"Error loading configuration: {e}")
    st.stop()

# --- UI Tabs ---
tab1, tab2 = st.tabs(["Generator", "Validation Results"])

with tab1:
    col1, col2 = st.columns([1, 1])
    with col1:
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
        if st.button("Generate STL File", type="primary", disabled=(uploaded_file is None)):
            st.session_state.validation_results = None  # Clear old results

            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            input_path = os.path.join(temp_dir, uploaded_file.name)
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            progress_bar = st.progress(0, text="Starting process...")
            status_text = st.empty()

            try:
                status_text.info("🎤 Processing Audio...")
                samples, sample_rate = audio_processing.process_audio(input_path, app_config)
                st.session_state.original_samples = samples
                st.session_state.sample_rate = sample_rate
                progress_bar.progress(33, text="Audio processing complete.")

                status_text.info("💿 Generating Groove Mesh...")
                record_mesh = geometry_generator.create_record_mesh(
                    samples, sample_rate, rpm_value, app_config
                )
                progress_bar.progress(66, text="Record mesh created.")

                status_text.info("💾 Saving STL file...")
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"record_{timestamp}.stl"
                output_path = os.path.join(temp_dir, output_filename)
                record_mesh.save(output_path)
                st.session_state.output_path = output_path
                progress_bar.progress(100, text="Process complete!")

                status_text.success(f"Your record is ready! Download below or check the Validation tab.")

            except Exception as e:
                st.error(f"An error occurred during generation: {e}")
                st.exception(e)
            finally:
                if os.path.exists(input_path):
                    os.remove(input_path)

        if st.session_state.output_path and os.path.exists(st.session_state.output_path):
            with open(st.session_state.output_path, "rb") as f:
                st.download_button(
                    label=f"Download {os.path.basename(st.session_state.output_path)}",
                    data=f,
                    file_name=os.path.basename(st.session_state.output_path),
                    mime="model/stl"
                )

    with col2:
        st.header("Configuration Preview")
        st.write("Current settings from `config.toml`:")
        st.json(app_config)


with tab2:
    st.header("Validate Your Record")
    if not st.session_state.output_path:
        st.warning("Please generate an STL file on the 'Generator' tab first.")
    else:
        st.info(f"File to validate: **{os.path.basename(st.session_state.output_path)}**")

        if st.button("Run Full Validation"):
            st.session_state.validation_results = None # Clear previous
            
            validation_status = st.empty()
            validation_progress = st.progress(0)

            try:
                results = validation.validate_stl(
                    st.session_state.output_path,
                    st.session_state.original_samples,
                    st.session_state.sample_rate,
                    app_config,
                    rpm_value,
                    progress_bar=validation_progress,
                    status_text=validation_status
                )
                st.session_state.validation_results = results
                validation_status.success("Validation complete!")
                validation_progress.progress(100)

            except Exception as e:
                st.error(f"An error occurred during validation: {e}")
                st.exception(e)

        if st.session_state.validation_results:
            results = st.session_state.validation_results
            st.subheader("Interactive 3D Model")
            st.plotly_chart(results['fig_3d'], use_container_width=True)

            st.subheader("Auditory Comparison")
            st.write("Original Processed Audio:")
            st.audio(results['original_wav'], format='audio/wav')
            st.write("Audio Extracted from STL:")
            st.audio(results['extracted_wav'], format='audio/wav')

            st.subheader("Visual Comparison")
            st.metric(
                label="Waveform Similarity (Correlation Score)",
                value=f"{results['similarity_score']:.4f}"
            )
            st.pyplot(results['fig_wave'])

