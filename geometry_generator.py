import numpy as np
from stl import mesh

def create_record_mesh(audio_samples, sample_rate, rpm, config):
    """
    Generates a 3D mesh of a playable vinyl record from audio samples.
    """
    dims = config['record_dimensions']
    geom = config['groove_geometry']

    radius = dims['record_diameter_mm'] / 2.0
    center_hole_radius = dims['center_hole_diameter_mm'] / 2.0
    thickness = dims['record_thickness_mm']
    pitch = geom['groove_pitch_mm']

    seconds_per_rotation = 60.0 / rpm
    audio_duration = len(audio_samples) / sample_rate
    num_rotations = audio_duration / seconds_per_rotation

    r_start = radius - dims['lead_in_groove_mm']
    r_end = center_hole_radius + 5

    theta_max = (r_start - r_end) * 2 * np.pi / pitch
    num_points = int(2000 * num_rotations)
    theta = np.linspace(0, theta_max, num_points)

    r = r_start - (pitch * theta / (2 * np.pi))
    x = r * np.cos(theta)
    y = r * np.sin(theta)

    audio_time = np.linspace(0, audio_duration, len(audio_samples))
    spiral_time = np.linspace(0, audio_duration, num_points)
    resampled_audio = np.interp(spiral_time, audio_time, audio_samples)

    z_mod = -geom['groove_depth_mm'] + (resampled_audio * geom['groove_depth_mm'] * geom['amplitude_scale'])

    dx, dy = np.gradient(x), np.gradient(y)
    norm = np.sqrt(dx**2 + dy**2)
    nx, ny = -dy/norm, dx/norm

    groove_half_width = geom['groove_top_width_mm'] / 2.0
    v_left = np.array([x - nx * groove_half_width, y - ny * groove_half_width, np.zeros(num_points)]).T
    v_right = np.array([x + nx * groove_half_width, y + ny * groove_half_width, np.zeros(num_points)]).T
    v_bottom = np.array([x, y, z_mod]).T

    faces = []
    for i in range(num_points - 1):
        faces.append([v_left[i], v_bottom[i+1], v_bottom[i]])
        faces.append([v_left[i], v_left[i+1], v_bottom[i+1]])
        faces.append([v_right[i], v_bottom[i], v_bottom[i+1]])
        faces.append([v_right[i], v_bottom[i+1], v_right[i+1]])

    body_vertices = []
    num_body_segments = 500
    for i in range(num_body_segments):
        angle = i * (2 * np.pi / num_body_segments)
        body_vertices.append([radius * np.cos(angle), radius * np.sin(angle), 0])
        body_vertices.append([radius * np.cos(angle), radius * np.sin(angle), -thickness])
        body_vertices.append([center_hole_radius * np.cos(angle), center_hole_radius * np.sin(angle), 0])
        body_vertices.append([center_hole_radius * np.cos(angle), center_hole_radius * np.sin(angle), -thickness])

    body_v_arr = np.array(body_vertices)

    for i in range(num_body_segments):
        j = (i + 1) % num_body_segments
        p_outer_top_i, p_outer_bot_i, p_inner_top_i, p_inner_bot_i = i*4, i*4+1, i*4+2, i*4+3
        p_outer_top_j, p_outer_bot_j, p_inner_top_j, p_inner_bot_j = j*4, j*4+1, j*4+2, j*4+3
        faces.append([body_v_arr[p_inner_top_i], body_v_arr[p_outer_top_j], body_v_arr[p_outer_top_i]])
        faces.append([body_v_arr[p_inner_top_i], body_v_arr[p_inner_top_j], body_v_arr[p_outer_top_j]])
        faces.append([body_v_arr[p_inner_bot_i], body_v_arr[p_outer_bot_i], body_v_arr[p_outer_bot_j]])
        faces.append([body_v_arr[p_inner_bot_i], body_v_arr[p_outer_bot_j], body_v_arr[p_inner_bot_j]])
        faces.append([body_v_arr[p_outer_top_i], body_v_arr[p_outer_bot_j], body_v_arr[p_outer_bot_i]])
        faces.append([body_v_arr[p_outer_top_i], body_v_arr[p_outer_top_j], body_v_arr[p_outer_bot_j]])
        faces.append([body_v_arr[p_inner_top_i], body_v_arr[p_inner_bot_i], body_v_arr[p_inner_bot_j]])
        faces.append([body_v_arr[p_inner_top_i], body_v_arr[p_inner_bot_j], body_v_arr[p_inner_top_j]])

    record_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    record_mesh.vectors = np.array(faces)
    return record_mesh
