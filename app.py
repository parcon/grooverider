# __project__ = "Audio-to-Vinyl STL Generator"
# __version__ = "1.1.0"
# __author__ = "Gemini AI"
# __filename__ = "app.py"
# __description__ = "Main Streamlit web interface for the application."

import streamlit as st
import os
from datetime import datetime
from st_viewer import st_viewer # Import the 3D viewer component

# Import project modules
import config
import audio_processing
import geometry_generator
import validation

# --- App Setup ---
st.set_page_config(
    page_title="Audio-to-Vinyl STL Generator",
    page_icon="💿",
    layout="wide" # Use wide layout for better 3D viewer display
)

# --- Session State Initialization ---
if 'output_path' not in st.session_state:
    st.session_state.output_path = None
if 'original_samples' not in st.session_state:
    st.session_state.original_samples = None
if 'sample_rate' not in st.session_state:
    st.session_state.sample_rate = None
if 'original_wav_bytes' not in st.session_state:
    st.session_state.original_wav_bytes = None
if 'extracted_wav_bytes' not in st.session_state:
    st.session_state.extracted_wav_bytes = None
if 'similarity_score' not in st.session_state:
    st.session_state.similarity_score = None
if 'comparison_fig' not in st.session_state:
    st.session_state.comparison_fig = None

st.title("💿 Audio-to-Vinyl STL Generator")
st.caption(f"Version {__version__}")


# --- UI Tabs ---
tab1, tab2 = st.tabs(["Generator", "Validation Results"])

# --- Generator Tab ---
with tab1:
    try:
        app_config = config.load_config()
    except Exception as e:
        st.error(f"Error loading configuration: {e}")
        st.stop()

    with st.sidebar:
        st.header("Configuration")
        st.write("Current settings from `config.toml`:")
        st.json(app_config)

    col1, col2 = st.columns(2)
    with col1:
        st.header("1. Upload Audio")
        uploaded_file = st.file_uploader("Choose an MP3 file", type=["mp3"], label_visibility="collapsed")
    
    with col2:
        st.header("2. Select Style")
        rpm_choice = st.radio("Playback Speed (RPM)", options=['33⅓ RPM', '45 RPM'], horizontal=True)
        rpm_value = 33.33 if '33' in rpm_choice else 45.0

    st.header("3. Generate Record")
    if st.button("Generate STL File", type="primary", use_container_width=True, disabled=(uploaded_file is None)):
        st.session_state.original_wav_bytes = None
        st.session_state.extracted_wav_bytes = None
        st.session_state.similarity_score = None
        st.session_state.comparison_fig = None

        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        input_path = os.path.join(temp_dir, uploaded_file.name)
        with open(input_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        progress_bar = st.progress(0, text="Starting process...")
        try:
            progress_bar.progress(10, text="Processing audio...")
            samples, sample_rate = audio_processing.process_audio(input_path, app_config)
            st.session_state.original_samples = samples
            st.session_state.sample_rate = sample_rate

            progress_bar.progress(40, text="Generating groove mesh...")
            record_mesh = geometry_generator.create_record_mesh(samples, sample_rate, rpm_value, app_config)

            progress_bar.progress(80, text="Saving STL file...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"record_{timestamp}.stl"
            output_path = os.path.join(temp_dir, output_filename)
            record_mesh.save(output_path)
            st.session_state.output_path = output_path
            
            progress_bar.progress(100, text="Process complete!")
            st.success("Generation successful! Switch to the 'Validation Results' tab to view and analyze your file.")
            
        except Exception as e:
            st.error(f"An error occurred during generation: {e}")
            st.exception(e)
        finally:
            if os.path.exists(input_path):
                os.remove(input_path)

# --- Validation Tab ---
with tab2:
    st.header("Validate Your Record")
    if not st.session_state.output_path:
        st.info("Please generate a record on the 'Generator' tab first.")
    else:
        st.markdown(f"**File to validate:** `{os.path.basename(st.session_state.output_path)}`")
        
        if st.button("Run Full Validation", key="run_validation", use_container_width=True):
            with st.spinner("Analyzing STL and audio... This may take a moment."):
                try:
                    rpm_value = 33.33 if '33' in st.session_state.get('rpm_choice', '33') else 45.0
                    
                    extracted_samples = validation.extract_audio_from_stl(st.session_state.output_path, app_config, rpm_value)
                    
                    st.session_state.original_wav_bytes = validation.convert_samples_to_wav_bytes(st.session_state.original_samples, st.session_state.sample_rate)
                    st.session_state.extracted_wav_bytes = validation.convert_samples_to_wav_bytes(extracted_samples, st.session_state.sample_rate)
                    
                    score, fig = validation.compare_audio_signals(st.session_state.original_samples, extracted_samples)
                    st.session_state.similarity_score = score
                    st.session_state.comparison_fig = fig

                except Exception as e:
                    st.error(f"An error occurred during validation: {e}")
                    st.exception(e)

        # --- Display Area ---
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Interactive 3D Preview")
            if os.path.exists(st.session_state.output_path):
                st_viewer(st.session_state.output_path, height=400, key="3d_viewer")
                with open(st.session_state.output_path, "rb") as f:
                    st.download_button("Download STL File", f, file_name=os.path.basename(st.session_state.output_path))
            else:
                st.warning("STL file not found. Please generate it first.")

        with col2:
            st.subheader("Analysis Results")
            if st.session_state.similarity_score is not None:
                st.metric("Waveform Similarity", f"{st.session_state.similarity_score:.4f}")
                st.write("Original Processed Audio:")
                st.audio(st.session_state.original_wav_bytes, format='audio/wav')
                st.write("Audio Extracted from STL:")
                st.audio(st.session_state.extracted_wav_bytes, format='audio/wav')
            else:
                st.info("Run validation to see analysis results.")

        if st.session_state.comparison_fig:
            st.subheader("Waveform Comparison")
            st.pyplot(st.session_state.comparison_fig)


