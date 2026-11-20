import cv2
import numpy as np
from config.settings import FACE_CASCADE_PATH, SMILE_CASCADE_PATH
from vision.face_detection import to_cv2_image

def load_mood_detectors():
    face_cascade = cv2.CascadeClassifier(str(FACE_CASCADE_PATH))
    smile_cascade = cv2.CascadeClassifier(str(SMILE_CASCADE_PATH))
    return face_cascade, smile_cascade

def analyze_mood(image_input) -> dict:
    """
    Analyze facial expression and mood from an image.
    Returns:
    {
        'mood': str,
        'emoji': str,
        'confidence': float,
        'summary': str,
        'faces_detected': int,
        'annotated_image': np.ndarray (RGB)
    }
    """
    face_cascade, smile_cascade = load_mood_detectors()
    img_bgr = to_cv2_image(image_input)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.15,
        minNeighbors=5,
        minSize=(60, 60)
    )

    annotated_bgr = img_bgr.copy()

    if len(faces) == 0:
        return {
            "mood": "No Face Detected",
            "emoji": "👤",
            "confidence": 0.0,
            "summary": "Could not find any clear faces in the image. Please ensure your face is well-lit and facing the camera.",
            "faces_detected": 0,
            "annotated_image": cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
        }

    detected_moods = []

    for i, (x, y, w, h) in enumerate(faces):
        roi_gray = gray[y:y + h, x:x + w]
        roi_color = annotated_bgr[y:y + h, x:x + w]

        # Lower half of face for mouth/smile detection
        mouth_roi_y = int(h * 0.5)
        mouth_roi = roi_gray[mouth_roi_y:h, :]

        smiles = smile_cascade.detectMultiScale(
            mouth_roi,
            scaleFactor=1.6,
            minNeighbors=15,
            minSize=(25, 25)
        )

        smile_count = len(smiles)
        if smile_count >= 2:
            mood = "Very Happy / Radiant"
            emoji = "😁"
            confidence = 0.92
            box_color = (0, 230, 255)  # Gold/Yellow
        elif smile_count == 1:
            mood = "Happy / Smiling"
            emoji = "😊"
            confidence = 0.85
            box_color = (0, 255, 128)  # Bright Green
        else:
            mood = "Calm / Neutral"
            emoji = "😐"
            confidence = 0.78
            box_color = (255, 180, 50)  # Cyan/Blue

        detected_moods.append((mood, emoji, confidence))

        # Draw stylish face rectangle
        cv2.rectangle(annotated_bgr, (x, y), (x + w, y + h), box_color, 2)

        # Draw mood badge
        badge_text = f"{mood} ({int(confidence * 100)}%)"
        cv2.rectangle(annotated_bgr, (x, y - 30), (x + min(w, 240), y), box_color, -1)
        cv2.putText(
            annotated_bgr,
            badge_text,
            (x + 5, y - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1,
            cv2.LINE_AA
        )

    # Primary mood is from first detected face
    primary_mood, primary_emoji, primary_conf = detected_moods[0]
    annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

    return {
        "mood": primary_mood,
        "emoji": primary_emoji,
        "confidence": primary_conf,
        "summary": f"Detected mood is {primary_mood} with approximately {int(primary_conf * 100)}% confidence.",
        "faces_detected": len(faces),
        "annotated_image": annotated_rgb
    }
