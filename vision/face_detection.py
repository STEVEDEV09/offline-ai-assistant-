import cv2
import numpy as np
from PIL import Image
import io
from config.settings import FACE_CASCADE_PATH, EYE_CASCADE_PATH

def load_face_detector():
    """Load face and eye cascade classifiers."""
    face_cascade = cv2.CascadeClassifier(str(FACE_CASCADE_PATH))
    eye_cascade = cv2.CascadeClassifier(str(EYE_CASCADE_PATH))
    return face_cascade, eye_cascade

def to_cv2_image(image_input) -> np.ndarray:
    """Convert uploaded file, bytes, or PIL image into OpenCV BGR numpy array."""
    if isinstance(image_input, np.ndarray):
        return image_input.copy()
    if isinstance(image_input, (bytes, bytearray)):
        nparr = np.frombuffer(image_input, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if hasattr(image_input, "read"):
        bytes_data = image_input.read()
        if hasattr(image_input, "seek"):
            image_input.seek(0)
        nparr = np.frombuffer(bytes_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if isinstance(image_input, Image.Image):
        rgb = np.array(image_input)
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    raise ValueError("Unsupported image input type")

def detect_faces(image_input) -> dict:
    """
    Detect faces in the input image.
    Returns:
    {
        'face_count': int,
        'faces': list of (x, y, w, h),
        'annotated_image': np.ndarray (RGB format for Streamlit),
        'status': str
    }
    """
    face_cascade, eye_cascade = load_face_detector()
    img_bgr = to_cv2_image(image_input)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(40, 40)
    )

    face_count = len(faces)
    annotated_bgr = img_bgr.copy()

    for i, (x, y, w, h) in enumerate(faces):
        # Draw sleek modern corner brackets / bounding box
        cv2.rectangle(annotated_bgr, (x, y), (x + w, y + h), (0, 255, 170), 2)

        # Label tag
        label = f"Face #{i + 1}"
        cv2.putText(
            annotated_bgr,
            label,
            (x, max(y - 10, 15)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 170),
            2,
            cv2.LINE_AA
        )

        # Eye detection inside face ROI
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = annotated_bgr[y:y + h, x:x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=10, minSize=(15, 15))
        for (ex, ey, ew, eh) in eyes[:2]:
            center = (ex + ew // 2, ey + eh // 2)
            cv2.circle(roi_color, center, int(ew * 0.4), (255, 180, 0), 2)

    # Convert back to RGB for Streamlit rendering
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

    return {
        "face_count": face_count,
        "faces": faces.tolist() if hasattr(faces, "tolist") else list(faces),
        "annotated_image": annotated_rgb,
        "status": f"Found {face_count} face{'s' if face_count != 1 else ''}."
    }
