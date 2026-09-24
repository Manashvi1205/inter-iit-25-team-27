import numpy as np
import cv2

# call img2wall with (img, d, z0, ori, M, K, ppm=None) to get rectified_img, (topleft_x, topleft_z)

def get_r_matrix(theta, phi):
    cam_z = np.array([
        np.sin(theta) * np.cos(phi),
        np.sin(theta) * np.sin(phi),
        np.cos(theta)
    ])

    cam_y = np.array([
        np.cos(theta) * np.cos(phi),
        np.cos(theta) * np.sin(phi),
        -np.sin(theta)
    ])

    cam_x = np.array([
        -np.sin(phi),
        np.cos(phi),
        0.0
    ])

    R = np.stack((cam_x, cam_y, cam_z), axis=1)

    return R

def get_cam_ray(u,v,K):

    f_x = K[0, 0]
    f_y = K[1, 1]
    c_x = K[0, 2]
    c_y = K[1, 2]

    ray_cam = np.array([
        (u - c_x) / f_x,
        (v - c_y) / f_y,
        1.0
    ])

    return ray_cam  

def pixel2wall(qr_c, d, z0, n, M, K): #M is matrix of coordinates, n is position number

    R = M[n]
    ray_cam = get_cam_ray(qr_c[0],qr_c[1],K)
    ray_loc = R @ ray_cam
    r_x, r_y, r_z = ray_loc

    t = d / r_y
    x_intersect = t * r_x
    z_intersect = t * r_z

    X_prime = x_intersect
    Z_prime = z_intersect + z0

    return (X_prime, Z_prime)

def rectify_image_to_wall(img, d, z0, theta_deg, phi_deg, K):
    """
    Un-warps a camera image onto the flat wall plane.
    
    Args:
        img: Source image (numpy array from cv2.imread)
        d: Distance to wall
        z0: Camera height
        theta_deg, phi_deg: Camera orientation
        K: Intrinsic matrix
        ppm: Pixels Per Meter for the output. If None, auto-calculated from K[0,0]/d.
        
    Returns:
        warped_img: The rectified image
        offset: Tuple (min_x, max_z) representing the top-left wall coordinate of this image.
    """
    if img is None:
        return None, None
        
    H, W = img.shape[:2]
    
    # 1. Auto-calculate resolution if needed (focal_pixels / distance_meters)
    ppm = K[0,0] / d 

    # 2. Determine Output Bounds
    # Project the 4 corners of the source image to the wall to see how "wide" the wall view is
    corners_uv = np.array([(0,0), (W,0), (W,H), (0,H)])
    Xs, Zs = [], []
    
    # Get rotation matrix for corner projection
    theta = np.deg2rad(theta_deg)
    phi = np.deg2rad(phi_deg)
    R = get_r_matrix(theta, phi)
    
    for u, v in corners_uv:
        ray_cam = get_cam_ray(u, v, K)
        ray_loc = R @ ray_cam
        r_x, r_y, r_z = ray_loc
        
        if np.abs(r_y) < 1e-6:
            continue  # Skip if parallel to wall
            
        t = d / r_y
        x_world = t * r_x
        z_world = t * r_z + z0
        Xs.append(x_world)
        Zs.append(z_world)
            
    if not Xs:
        return None, None  # Camera not looking at wall
    
    # Define the bounding box on the wall
    min_x, max_x = min(Xs), max(Xs)
    min_z, max_z = min(Zs), max(Zs)
    
    # Calculate output image dimensions
    out_W = int(np.ceil((max_x - min_x) * ppm))
    out_H = int(np.ceil((max_z - min_z) * ppm))
    
    if out_W <= 0 or out_H <= 0:
        return None, None

    # 3. Forward mapping: project all input pixels to world coordinates
    # Create meshgrids for all input pixel coordinates
    u_coords, v_coords = np.meshgrid(np.arange(W), np.arange(H))
    u_flat = u_coords.flatten()
    v_flat = v_coords.flatten()
    
    # Vectorized camera ray computation for all pixels
    f_x, f_y = K[0, 0], K[1, 1]
    c_x, c_y = K[0, 2], K[1, 2]
    
    ray_cam = np.stack([
        (u_flat - c_x) / f_x,
        (v_flat - c_y) / f_y,
        np.ones_like(u_flat)
    ], axis=0)  # Shape: (3, H*W)
    
    # Get rotation matrix and apply to all rays at once (R already computed above)
    # R is already computed from corner projection, reuse it
    ray_loc = R @ ray_cam  # Shape: (3, H*W)
    
    # Extract components and compute world coordinates
    r_x, r_y, r_z = ray_loc[0], ray_loc[1], ray_loc[2]
    
    # Avoid division by zero
    r_y = np.where(np.abs(r_y) < 1e-6, 1e-6, r_y)
    t = d / r_y
    
    x_world = t * r_x
    z_world = t * r_z + z0
    
    # 4. Map world coordinates to output image coordinates
    i_out = np.clip((max_z - z_world) / (max_z - min_z) * (out_H - 1), 0, out_H - 1).astype(int)
    j_out = np.clip((x_world - min_x) / (max_x - min_x) * (out_W - 1), 0, out_W - 1).astype(int)
    
    # 5. Create output image and use advanced indexing to place pixels
    warped_img = np.zeros((out_H, out_W, img.shape[2]) if len(img.shape) == 3 else (out_H, out_W), dtype=img.dtype)
    
    if len(img.shape) == 3:
        warped_img[i_out, j_out] = img[v_flat, u_flat]
    else:
        warped_img[i_out, j_out] = img[v_flat, u_flat]
    
    return warped_img, ppm, (min_x, max_z)

def img2rack(img, d, z0, ori, K):
    if(ori == 2):
        theta = 0
        phi = 90
    elif(ori == 1):
        theta = 90
        phi = 90
    elif(ori == 0):
        theta = 180
        phi = 90
    projection, scale, (x_topleft, y_topleft) = rectify_image_to_wall(img, d, z0, theta, phi, K)
    return projection, scale, (x_topleft, y_topleft)