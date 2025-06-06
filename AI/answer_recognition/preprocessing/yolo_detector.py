from PIL import Image
from typing import List, Tuple, Optional

# config와 data_structures는 상위 디렉토리 또는 answer_recognition 패키지 레벨에서 가져와야 함
# 현재 yolo_detector.py는 answer_recognition/preprocessing/ 안에 위치
from ..config import yolo_model, YOLO_CLASS_QN, YOLO_CLASS_ANS
from ..data_structures import DetectedArea

def yolo_predict_and_extract_areas_pil(
    original_pil_image: Image.Image,
    original_image_identifier: str
) -> Tuple[Optional[DetectedArea], Optional[DetectedArea]]:
    """
    원본 PIL Image에 YOLO 예측을 수행하여 qn 영역과 ans 영역 정보를 DetectedArea 객체로 반환.
    이 함수는 config.py에 로드된 yolo_model을 사용합니다.
    항상 각 타입별로 하나의 객체만 반환하거나, 없으면 None을 반환합니다.
    """
    if not yolo_model:
        print("YOLO model is not loaded. Cannot perform detection.")
        return None, None

    qn_area: Optional[DetectedArea] = None
    ans_area: Optional[DetectedArea] = None

    results = yolo_model(original_pil_image, verbose=False)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
            
            cropped_pil_image = original_pil_image.crop((x1, y1, x2, y2))
            area_type_str = ""

            if class_id == YOLO_CLASS_QN and qn_area is None:
                area_type_str = "question_number"
                qn_area = DetectedArea(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    area_type=area_type_str,
                    image_obj=cropped_pil_image,
                    original_image_ref=original_image_identifier
                )
            elif class_id == YOLO_CLASS_ANS and ans_area is None:
                area_type_str = "answer"
                ans_area = DetectedArea(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    area_type=area_type_str,
                    image_obj=cropped_pil_image,
                    original_image_ref=original_image_identifier
                )
            
            if qn_area is not None and ans_area is not None:
                break
        if qn_area is not None and ans_area is not None:
            break
    
    return qn_area, ans_area 