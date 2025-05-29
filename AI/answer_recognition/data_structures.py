from typing import Tuple, TypedDict
from PIL import Image

# --- Data Structures ---
class DetectedArea(TypedDict):
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2) - 원본 이미지 기준 좌표
    class_id: int
    area_type: str                   # "question_number" 또는 "answer"
    image_obj: Image.Image           # Crop된 PIL Image 객체
    original_image_ref: str          # 어떤 원본 이미지에서 왔는지 식별자 (예: 파일명) 