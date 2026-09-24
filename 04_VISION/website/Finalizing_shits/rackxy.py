def sanidhya(x0,z0):
    return x0,z0

def rack_coordinates_from_uv_center(xz_topleft, uv_center, scale, z0, x0):
    x_center, y_center = uv_center
    x_topleft, z_topleft = xz_topleft
    x_topleft = x_topleft + x0
    z_topleft = z_topleft + z0
    x_center = x_center * scale + x_topleft
    z_center = z_center * scale + z_topleft
    return x_center, y_center
