# __project__ = "Audio-to-Vinyl STL Generator"
__version__ = "1.5.1"
__author__ = "Gemini AI"
__filename__ = "geometry_generator.py"
# __description__ = "Generates a single, solid, manifold 3D mesh for the vinyl record."

import numpy as np
from stl import mesh
from scipy.spatial import KDTree

def create_record_mesh(samples, sample_rate, rpm, config):
    """
    Generates a single, manifold, solid 3D mesh for a vinyl record by
    creating a clean topology and displacing the top vertices for the groove.
    """
    dims = config['record_dimensions']
    geom = config['groove_geometry']

    # --- Disc Parameters ---
    radius = dims['record_diameter_mm'] / 2.0
    hole_radius = dims['center_hole_diameter_mm'] / 2.0
    thickness = dims['record_thickness_mm']
    
    # --- Spiral Path for Groove Centerline (used for displacement) ---
    r_start = radius - dims['lead_in_groove_mm']
    total_samples = len(samples)
    seconds_per_rotation = 60.0 / rpm
    samples_per_rotation = int(sample_rate * seconds_per_rotation)
    total_rotations = total_samples / samples_per_rotation
    r_end = r_start - (total_rotations * geom['groove_pitch_mm'])
    
    theta_spiral = np.linspace(0, total_rotations * 2 * np.pi, num=total_samples)
    r_spiral = np.linspace(r_start, r_end, num=total_samples)
    x_spiral = r_spiral * np.cos(theta_spiral)
    y_spiral = r_spiral * np.sin(theta_spiral)
    
    amplitude = geom['amplitude_scale'] * geom['groove_depth_mm']
    z_spiral_center = -geom['groove_depth_mm'] + (samples * amplitude)

    spiral_tree = KDTree(np.column_stack([x_spiral, y_spiral]))

    # --- Generate a High-Resolution Grid of Vertices ---
    num_radial_steps = 300
    num_angular_steps = 720
    
    radii = np.linspace(hole_radius, radius, num_radial_steps)
    thetas = np.linspace(0, 2 * np.pi, num_angular_steps, endpoint=False) # Important: no endpoint
    
    R, T = np.meshgrid(radii, thetas)
    X = R * np.cos(T)
    Y = R * np.sin(T)
    Z = np.zeros_like(X)

    # --- Displace Top Vertices to Create the Groove ---
    top_verts_flat = np.vstack([X.ravel(), Y.ravel(), Z.ravel()]).T
    distances, indices = spiral_tree.query(top_verts_flat[:, :2])
    
    groove_width = geom['groove_pitch_mm'] * 0.7
    mask = distances < groove_width
    displacement = (z_spiral_center[indices[mask]]) * (1 - distances[mask] / groove_width)
    top_verts_flat[mask, 2] = displacement
    
    # --- Create Full Set of Vertices (Top and Bottom) ---
    bottom_verts_flat = top_verts_flat.copy()
    bottom_verts_flat[:, 2] -= thickness
    all_verts = np.vstack([top_verts_flat, bottom_verts_flat])
    
    # --- Generate Faces for a Solid, Manifold Mesh ---
    faces = []
    num_verts_per_surface = X.size
    
    # Generate faces for the top and bottom surfaces
    for j in range(num_angular_steps):
        j_next = (j + 1) % num_angular_steps
        for i in range(num_radial_steps - 1):
            p1 = j * num_radial_steps + i
            p2 = j * num_radial_steps + (i + 1)
            p3 = j_next * num_radial_steps + (i + 1)
            p4 = j_next * num_radial_steps + i
            
            faces.append([p1, p3, p2])
            faces.append([p1, p4, p3])
            
            p1b, p2b, p3b, p4b = p1 + num_verts_per_surface, p2 + num_verts_per_surface, p3 + num_verts_per_surface, p4 + num_verts_per_surface
            faces.append([p1b, p2b, p3b])
            faces.append([p1b, p3b, p4b])

    # Generate faces for the inner and outer walls
    for j in range(num_angular_steps):
        j_next = (j + 1) % num_angular_steps
        
        # Outer wall
        p1 = j * num_radial_steps + (num_radial_steps - 1)
        p2 = j_next * num_radial_steps + (num_radial_steps - 1)
        p1b = p1 + num_verts_per_surface
        p2b = p2 + num_verts_per_surface
        faces.append([p1, p2b, p2])
        faces.append([p1, p1b, p2b])
        
        # Inner wall
        p1 = j * num_radial_steps
        p2 = j_next * num_radial_steps
        p1b = p1 + num_verts_per_surface
        p2b = p2 + num_verts_per_surface
        faces.append([p1, p2, p2b])
        faces.append([p1, p2b, p1b])

    # --- Create and return the final mesh ---
    faces = np.array(faces)
    record_mesh = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3):
            record_mesh.vectors[i][j] = all_verts[f[j], :]
            
    return record_mesh

