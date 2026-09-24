import cv2
import os
import yolo

def make_square_canvas(image, padding_color=(255, 255, 255)):
    """
    Pads the shorter side of the image with the specified color
    to create a perfect 1:1 aspect ratio square.
    This preserves the 'Finder Pattern' ratios (1:1:3:1:1).
    """
    h, w = image.shape[:2]

    if h == w:
        return image

    # Determine the target size (largest dimension)
    max_dim = max(h, w)

    # Calculate total padding needed
    delta_w = max_dim - w
    delta_h = max_dim - h

    # Distribute padding (integer division)
    top = delta_h // 2
    bottom = delta_h - top
    left = delta_w // 2
    right = delta_w - left

    # Apply constant border (White to extend Quiet Zone)
    squared_img = cv2.copyMakeBorder(
        image,
        top, bottom, left, right,
        cv2.BORDER_CONSTANT,
        value=padding_color
    )

    return squared_img

def crop_qr(original_image, detections, crop_path, height): #takes the cv2.imwritten images and then processes for all bbox
    """
    Full Pipeline:
    1. Extract Bbox
    2. Pad by 20%
    3. Square the Geometry
    4. Resize to 400x400 (Lanczos)
    5. Enhance
    """

    """crop_img_dir = "cropped_images"
    os.makedirs(crop_img_dir, exist_ok=True)"""

    for detection in detections:
        x1, y1, x2, y2 = detection['bbox_xyxy']
    
        img_h, img_w = original_image.shape[:2]

        x_cent, y_cent= yolo.get_centroid(x1, y1, x2, y2)
        
        img_name=f"{x_cent}_{y_cent}_{str(height)}"
        # --- STEP 1: CALCULATE 0.2 PADDING ---
        box_w = x2 - x1
        box_h = y2 - y1

        pad_x = int(box_w * 0.2)
        pad_y = int(box_h * 0.2)

        # --- STEP 2: CROP WITH BOUNDARY CHECKS ---
        # Ensure we don't crop outside the image
        crop_x1 = max(0, x1 - pad_x)
        crop_y1 = max(0, y1 - pad_y)
        crop_x2 = min(img_w, x2 + pad_x)
        crop_y2 = min(img_h, y2 + pad_y)

        cropped_roi = original_image[crop_y1:crop_y2, crop_x1:crop_x2]

        # --- STEP 3: SQUARE THE GEOMETRY ---
        # Critical for preserving scanning ratios
        squared_roi = make_square_canvas(cropped_roi, padding_color=(255, 255, 255))

        path=os.path.join(crop_path,f'{img_name}.jpg') #MUST RESOLVE, WHAT IF 2 DIFF QRS HAVE SAME CENTRES IN 2 DIFEERENT RACKS. RESOLVED USING HEIGHT. NOT ORIENTATION AS WE WANT TO REMOVE THE REDUNDANCY AT A HEIGHT.
        cv2.imwrite(path, squared_roi)

def annotate_img(img,detections,anno_path, height, orientation):#img is cv2.imwritten
    # Draw the detections
    for detection in detections:
        x1, y1, x2, y2 = detection['bbox_xyxy']
        confidence = detection['confidence']
        im2=img.copy()
        cv2.rectangle(im2, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(im2, f'{confidence:.2f}', (int(x1), int(y1) - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                    fontScale=1, color=(0, 255, 0), thickness=2)
    # Save the results
    path=os.path.join(anno_path,f"{height}_{orientation[0]}_{orientation[1]}.jpg")
    cv2.imwrite(path, im2)