import homo
import rackxy
import yolo
import reader
import numpy as np

def img2write(img, x0, d, z0, ori, K):
    projection, scale, xz_topleft = homo.img2rack(img, d, z0, ori, K)
    qr_array = yolo.make_qr_array(projection)
    output_array = []
    for qr in qr_array:
        qr_img, qr_coordinates = qr
        qr_coordinates = rackxy.rack_coordinates_from_uv_center(xz_topleft, qr_coordinates, scale, z0, x0)
        qr_payload = reader.read(qr_img)
        output_array.append(qr_payload, qr_coordinates)
    return output_array


if __name__ == "__main__":
    IMG = 'imgs/test.jpg'
    #PARAMETERS
    x0=0
    z0=1
    ori=0
    d=1
    K = np.array([
    [1000.0,    0.0, 640.0],
    [   0.0, 1000.0, 360.0],
    [   0.0,    0.0,   1.0]
], dtype=np.float32)

    img2write(IMG, x0, d, z0, ori, K)

    

