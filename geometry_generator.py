# __project__ = "Audio-to-Vinyl STL Generator"
# __version__ = "1.1.0"
# __author__ = "Gemini AI"
# __filename__ = "geometry_generator.py"
# __description__ = "Generates the 3D record mesh from audio samples."

import numpy as np
from stl import mesh

def create_record_mesh(samples, sample_rate, rpm, config):
    """
    Generates a 3D mesh for a vinyl record from processed audio samples.
    """
    dims = config['record_dimensions']
    geom = config['groove_geometry']
    
    # Physical constants
    radius = dims['record_diameter_mm'] / 2.0
    thickness = dims['record_thickness_mm']
    center_hole_radius = dims['center_hole_diameter_mm'] / 2.0
    
    # Groove constants
    pitch = geom['groove_pitch_mm']
    base_depth = -geom['groove_depth_mm']
    modulation_range = geom['groove_depth_mm'] * geom['amplitude_scale']

    # Calculate timing and spiral parameters
    seconds_per_rotation = 60.0 / rpm
    samples_per_rotation = int(seconds_per_rotation * sample_rate)
    num_rotations = len(samples) // samples_per_rotation
    
    # Generate the full spiral path
    vertices = []
    r_start = radius - dims['lead_in_groove_mm']
    
    for i in range(num_rotations):
        r = r_start - i * pitch
        segment_samples = samples[i * samples_per_rotation : (i + 1) * samples_per_rotation]
        theta = np.linspace(0, 2 * np.pi, len(segment_samples))
        
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = base_depth + modulation_range * segment_samples
        
        vertices.extend(list(zip(x, y, z)))

    vertices = np.array(vertices)
    num_verts = len(vertices)
    
    # Create faces for the groove
    faces = []
    for i in range(num_verts - 1):
        if np.linalg.norm(vertices[i] - vertices[i+1]) < pitch * 2:
             # Create a quad between adjacent vertices and their counterparts on the next rotation
            if i < num_verts - samples_per_rotation -1:
                p1, p2 = vertices[i], vertices[i+1]
                p3 = vertices[i + samples_per_rotation]
                p4 = vertices[i + samples_per_rotation + 1]
                faces.append([p1, p2, p3])
                faces.append([p2, p4, p3])
    
    # Create the record body (a simple cylinder for now)
    body_faces = []
    num_body_segments = 200
    angle_step = 2 * np.pi / num_body_segments
    
    # Top and bottom faces
    for i in range(num_body_segments):
        theta1 = i * angle_step
        theta2 = (i + 1) * angle_step
        
        # Outer rim
        p1 = [radius * np.cos(theta1), radius * np.sin(theta1), 0]
        p2 = [radius * np.cos(theta2), radius * np.sin(theta2), 0]
        p3 = [radius * np.cos(theta1), radius * np.sin(theta1), -thickness]
        p4 = [radius * np.cos(theta2), radius * np.sin(theta2), -thickness]
        body_faces.append([p1, p2, p3])
        body_faces.append([p2, p4, p3])

        # Inner hole
        p5 = [center_hole_radius * np.cos(theta1), center_hole_radius * np.sin(theta1), 0]
        p6 = [center_hole_radius * np.cos(theta2), center_hole_radius * np.sin(theta2), 0]
        p7 = [center_hole_radius * np.cos(theta1), center_hole_radius * np.sin(theta1), -thickness]
        p8 = [center_hole_radius * np.cos(theta2), center_hole_radius * np.sin(theta2), -thickness]
        body_faces.append([p5, p6, p7])
        body_faces.append([p6, p8, p7])


    all_faces = faces + body_faces
    
    record_mesh = mesh.Mesh(np.zeros(len(all_faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(all_faces):
        record_mesh.vectors[i] = np.array(f)
        
    return record_mesh


