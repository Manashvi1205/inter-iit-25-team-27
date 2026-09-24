import cv2
import numpy as np

def get_centroid(x1, y1, x2, y2):
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    return int(cx), int(cy)

def make_qr_array(image):
    """
    Detects all QR codes in an image and returns an array of tuples.
    Each tuple contains:
        - First element: cropped screenshot of the QR code
        - Second element: (u, v) coordinate tuple of the centroid
    
    Args:
        image: Input image (numpy array, typically from cv2.imread)
    
    Returns:
        List of tuples: [(qr_screenshot, (u, v)), ...]
    """
    if image is None:
        return []
    
    # Initialize QR code detector
    detector = cv2.QRCodeDetector()
    
    # Detect and decode QR codes
    retval, _, points, _ = detector.detectAndDecodeMulti(image)
    
    qr_array = []
    
    if retval and points is not None and len(points) > 0:
        img_h, img_w = image.shape[:2]
        
        # Handle both single and multiple QR codes
        # points can be a list of arrays or a single array
        if not isinstance(points, (list, tuple)):
            points = [points]
        
        for i, qr_points in enumerate(points):
            if qr_points is None or len(qr_points) == 0:
                continue
            
            # Convert points to numpy array and ensure proper shape
            qr_points = np.array(qr_points)
            if qr_points.shape != (4, 2):
                # Try to reshape if needed
                if qr_points.size == 8:  # 4 points * 2 coordinates
                    qr_points = qr_points.reshape(4, 2)
                else:
                    continue
            
            # Convert points to integer coordinates
            qr_points = qr_points.astype(int)
            
            # Calculate bounding box from QR code points
            x_coords = qr_points[:, 0]
            y_coords = qr_points[:, 1]
            x1 = int(np.min(x_coords))
            y1 = int(np.min(y_coords))
            x2 = int(np.max(x_coords))
            y2 = int(np.max(y_coords))
            
            # Calculate centroid
            u, v = get_centroid(x1, y1, x2, y2)
            
            # Add 20% padding (matching crop_qr function)
            box_w = x2 - x1
            box_h = y2 - y1
            pad_x = int(box_w * 0.2)
            pad_y = int(box_h * 0.2)
            
            # Crop with boundary checks
            crop_x1 = max(0, x1 - pad_x)
            crop_y1 = max(0, y1 - pad_y)
            crop_x2 = min(img_w, x2 + pad_x)
            crop_y2 = min(img_h, y2 + pad_y)
            
            # Extract cropped QR code region
            qr_screenshot = image[crop_y1:crop_y2, crop_x1:crop_x2].copy()
            
            # Add to array
            qr_array.append((qr_screenshot, (u, v)))
    
    return qr_array