# Groove Rider
# Copyright (c) 2024
#
# This script provides the main user interface for Groove Rider using Streamlit.
# It allows users to upload an audio file, configure record parameters, and
# generate a 3D-printable STL file of a vinyl-style record.

import streamlit as st
import os
import datetime
import audio_processing
import geometry_generator
import validation
from config import AppConfig

# --- Page Configuration ---
st.set_page_config(
    page_title="Groove Rider",
    page_icon="🎶",
    layout="wide"
)

st.title("Groove Rider 🎶")
st.write("Convert your audio files into 3D-printable vinyl-style records.")

# --- Load Configuration ---
cfg = AppConfig('config.toml')

# --- Sidebar for Configuration ---
st.sidebar.header("Record Configuration")
uploaded_file = st.sidebar.file_uploader(
    "Choose an audio file (MP3, WAV, etc.)",
    type=['mp3', 'wav', 'ogg', 'flac']
)

# Update the AppConfig object directly from the UI
st.sidebar.subheader("Physical Dimensions (mm)")
cfg.record['diameter'] = st.sidebar.number_input("Diameter", value=cfg.record['diameter'], format="%.1f")
cfg.record['thickness'] = st.sidebar.number_input("Thickness", value=cfg.record['thickness'], format="%.1f")
cfg.record['hole_diameter'] = st.sidebar.number_input("Center Hole Diameter", value=cfg.record['hole_diameter'], format="%.1f")

st.sidebar.subheader("Groove Properties")
cfg.record['groove_width'] = st.sidebar.number_input("Groove Width (mm)", value=cfg.record['groove_width'], format="%.3f", step=0.001)
cfg.record['groove_depth'] = st.sidebar.number_input("Max Groove Depth (mm)", value=cfg.record['groove_depth'], format="%.3f", step=0.001)
cfg.audio['amplitude_scale'] = st.sidebar.slider("Amplitude Scale", 0.1, 5.0, cfg.audio['amplitude_scale'])

# --- Main Application Logic ---
if uploaded_file is not None and st.sidebar.button("Generate Record"):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Processing Steps")
        with st.spinner("Processing audio..."):
            try:
                samples = audio_processing.load_and_process_audio(uploaded_file, cfg)
                st.success("Audio processed successfully!")
            except Exception as e:
                st.error(f"Error processing audio: {e}")
                st.stop()

        with st.spinner("Generating 3D model... This might take a moment."):
            try:
                record_mesh = geometry_generator.create_record_geometry(samples, cfg)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                temp_dir = "temp"
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                file_path = os.path.join(temp_dir, f"record_{timestamp}.stl")
                geometry_generator.save_mesh_as_stl(record_mesh, file_path)
                st.success(f"3D model generated!")
            except Exception as e:
                st.error(f"Error generating 3D model: {e}")
                st.stop()

        # --- Re-enabled Validation Step ---
        with st.spinner("Validating 3D model..."):
            try:
                validation_results = validation.validate_stl(file_path)
                if not validation_results["errors"]:
                    st.success("Validation successful! The model appears to be printable.")
                else:
                    st.error("Validation failed. The model has issues that may prevent printing.")
                    for error in validation_results["errors"]:
                        st.warning(error)
            except Exception as e:
                st.error(f"An error occurred during validation: {e}")

    with col2:
        st.subheader("Results & Download")
        if 'file_path' in locals() and os.path.exists(file_path):
             with open(file_path, "rb") as f:
                st.download_button(
                    label="Download STL File",
                    data=f,
                    file_name=os.path.basename(file_path),
                    mime="model/stl",
                )
             if 'validation_results' in locals():
                 st.json(validation_results)
else:
    st.info("Upload an audio file and click 'Generate Record' to begin.")

