# Groove Rider
# Copyright (c) 2024
#
# This script is responsible for generating the 3D geometry of the vinyl record
# from the processed audio data. It uses numpy-stl to create the mesh.

import numpy as np
from stl import mesh
from config import AppConfig

def create_record_geometry(samples: np.ndarray, cfg: AppConfig) -> mesh.Mesh:
    """
    Generates the 3D mesh for a vinyl-style record from audio samples by
    building a single, unified list of vertices and faces.
    """
    # --- Configuration Parameters ---
    record_config = cfg.config['record']
    audio_config = cfg.config['audio']
    
    record_radius = record_config['diameter'] / 2
    thickness = record_config['thickness']
    hole_radius = record_config['hole_diameter'] / 2
    groove_width = record_config['groove_width']
    groove_depth = record_config['groove_depth']
    amplitude_scale = audio_config.get('amplitude_scale', 1.0)

    # Define track area
    outer_radius = record_radius - record_config.get('lead_in_width', 5)
    inner_radius = hole_radius + record_config.get('lead_out_width', 5)
    track_width = outer_radius - inner_radius

    # --- 1. Generate Base Disc Vertices & Faces ---
    all_vertices = []
    all_faces = []
    
    num_sides_disc = 200
    angles = np.linspace(0, 2 * np.pi, num_sides_disc, endpoint=False)

    # Add outer-ring vertices (top and bottom)
    for angle in angles:
        x, y = record_radius * np.cos(angle), record_radius * np.sin(angle)
        all_vertices.append([x, y, thickness / 2])
        all_vertices.append([x, y, -thickness / 2])

    # Add inner-hole vertices (top and bottom)
    for angle in angles:
        x, y = hole_radius * np.cos(angle), hole_radius * np.sin(angle)
        all_vertices.append([x, y, thickness / 2])
        all_vertices.append([x, y, -thickness / 2])

    # Create faces for disc walls and surfaces
    for i in range(num_sides_disc):
        next_i = (i + 1) % num_sides_disc
        
        # Outer wall faces
        all_faces.append([i * 2, next_i * 2, i * 2 + 1])
        all_faces.append([next_i * 2, next_i * 2 + 1, i * 2 + 1])
        
        # Inner wall faces
        off = num_sides_disc * 2
        all_faces.append([off + i * 2, off + i * 2 + 1, off + next_i * 2])
        all_faces.append([off + next_i * 2, off + i * 2 + 1, off + next_i * 2 + 1])
        
        # Top surface faces
        all_faces.append([i * 2, off + i * 2, off + next_i * 2])
        all_faces.append([i * 2, off + next_i * 2, next_i * 2])
        
        # Bottom surface faces
        all_faces.append([i * 2 + 1, off + next_i * 2 + 1, off + i * 2 + 1])
        all_faces.append([i * 2 + 1, next_i * 2 + 1, off + next_i * 2 + 1])

    # --- 2. Generate Spiral Groove ---
    num_rotations = int(track_width / groove_width)
    total_angle = 2 * np.pi * num_rotations
    num_points_spiral = len(samples)
    
    theta = np.linspace(0, total_angle, num_points_spiral)
    r = np.linspace(outer_radius, inner_radius, num_points_spiral)
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    
    z_modulation = samples * groove_depth * amplitude_scale
    z_center = (thickness / 2) - (groove_depth / 2) - z_modulation

    # --- 3. Create Groove Mesh by adding to the main vertex/face lists ---
    for i in range(1, num_points_spiral):
        direction = np.array([x[i] - x[i-1], y[i] - y[i-1], 0])
        norm = np.linalg.norm(direction)
        if norm == 0: continue
        
        perp = np.array([-direction[1], direction[0], 0]) / norm
        
        v1 = np.array([x[i-1], y[i-1], z_center[i-1]]) - perp * (groove_width / 2)
        v2 = np.array([x[i-1], y[i-1], z_center[i-1]]) + perp * (groove_width / 2)
        v3 = np.array([x[i], y[i], z_center[i]]) - perp * (groove_width / 2)
        v4 = np.array([x[i], y[i], z_center[i]]) + perp * (groove_width / 2)

        # Get the current length of the vertex list to use as the base index
        idx = len(all_vertices)
        
        all_vertices.extend([v1, v2, v3, v4])
        
        # Add faces using the correct, globally incrementing base index
        all_faces.append([idx, idx + 2, idx + 1])
        all_faces.append([idx + 1, idx + 2, idx + 3])

    # --- 4. Create the final mesh from the combined lists ---
    vertices_np = np.array(all_vertices)
    faces_np = np.array(all_faces)
    
    combined_mesh = mesh.Mesh(np.zeros(faces_np.shape[0], dtype=mesh.Mesh.dtype))
    combined_mesh.vectors = vertices_np[faces_np]
    
    return combined_mesh

def save_mesh_as_stl(mesh_data: mesh.Mesh, file_path: str):
    """Saves a numpy-stl mesh object to an STL file."""
    mesh_data.save(file_path)

