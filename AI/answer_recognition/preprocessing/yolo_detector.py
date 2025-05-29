from PIL import Image
from typing import List, Tuple

# config와 data_structures는 상위 디렉토리 또는 answer_recognition 패키지 레벨에서 가져와야 함
# 현재 yolo_detector.py는 answer_recognition/preprocessing/ 안에 위치
from ..config import yolo_model, YOLO_CLASS_QN, YOLO_CLASS_ANS
from ..data_structures import DetectedArea

def yolo_predict_and_extract_areas_pil(
    original_pil_image: Image.Image,
    original_image_identifier: str
) -> Tuple[List[DetectedArea], List[DetectedArea]]:
    """
    원본 PIL Image에 YOLO 예측을 수행하여 qn 영역과 ans 영역 정보를 DetectedArea 객체 리스트로 반환.
    이 함수는 config.py에 로드된 yolo_model을 사용합니다.
    """
    if not yolo_model:
        print("YOLO model is not loaded. Cannot perform detection.")
        return [], []

    qn_areas: List[DetectedArea] = []
    ans_areas: List[DetectedArea] = []

    results = yolo_model(original_pil_image, verbose=False)

    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
            
            cropped_pil_image = original_pil_image.crop((x1, y1, x2, y2))
            area_type_str = ""

            if class_id == YOLO_CLASS_QN:
                area_type_str = "question_number"
                area_info = DetectedArea(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    area_type=area_type_str,
                    image_obj=cropped_pil_image,
                    original_image_ref=original_image_identifier
                )
                qn_areas.append(area_info)
            elif class_id == YOLO_CLASS_ANS:
                area_type_str = "answer"
                area_info = DetectedArea(
                    bbox=(x1, y1, x2, y2),
                    class_id=class_id,
                    area_type=area_type_str,
                    image_obj=cropped_pil_image,
                    original_image_ref=original_image_identifier
                )
                ans_areas.append(area_info)
    
    # y1 좌표 기준으로 정렬 (일반적으로 필요 없을 수 있으나, 순서 보장을 위해)
    qn_areas.sort(key=lambda area: area['bbox'][1])
    ans_areas.sort(key=lambda area: area['bbox'][1])

    return qn_areas, ans_areas 