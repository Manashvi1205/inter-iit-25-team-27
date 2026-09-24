import cv2
import os
"import some init for wechat?"
def bin_thresholding(image, threshold=130):
  if threshold==-1:
    _, thresholded =cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  else:
    _, thresholded =cv2.threshold(image, 140, 255, cv2.THRESH_BINARY)
  return thresholded


def enhance_qr_clarity(image):
    """
    Applies non-AI enhancement: CLAHE for contrast and Unsharp Mask for edges.
    """
    # 1. Convert to Grayscale
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image

    # 2. Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # clipLimit=2.0 prevents noise amplification
    # tileGridSize=(8,8) is standard for localizing contrast adjustments
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast_enhanced = clahe.apply(gray)

    # 3. Apply Unsharp Masking
    # Logic: Sharpened = Original + (Original - Blurred) * Amount
    gaussian = cv2.GaussianBlur(contrast_enhanced, (0, 0), 2.0)
    sharpened = cv2.addWeighted(contrast_enhanced, 1.5, gaussian, -0.5, 0)

    return sharpened

def enhance_fin(squared_roi):
    resized_roi = cv2.resize(squared_roi, (400, 400), interpolation=cv2.INTER_LANCZOS4)

    # --- STEP 5: ENHANCEMENT ---
    semi_final_result = enhance_qr_clarity(resized_roi)
    final_result = bin_thresholding(semi_final_result, threshold=140)

    return final_result

def detect_fin(final_result):
    if final_result is None:
        print("Error: Could not load image 'qr_baddest.png'. Please ensure the file exists and the path is correct.")
    else:
        print("Image loaded and converted to grayscale successfully.")

    res, points = we_chat_decoder.detectAndDecode(final_result)

    if len(res)>0:
      print(f"success {res}")
    else:
      print(f"failed")
      os.remove(path)
    
    return res