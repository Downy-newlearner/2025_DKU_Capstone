"""
YOLO 검출 모듈
"""
import logging
from typing import Optional, Tuple
from PIL import Image
from ultralytics import YOLO

from .config import STUDENT_ID_CLASS_ID


def detect_student_id_area(
    yolo_model: YOLO,
    pil_image: Image.Image,
    image_file: str,
    logger: logging.Logger
) -> Tuple[Optional[Image.Image], float, Optional[str]]:
    """
    YOLO로 학번 영역 검출 및 크롭.
    
    Args:
        yolo_model: YOLO 모델 객체
        pil_image: PIL Image 객체
        image_file: 이미지 파일명 (로깅용)
        logger: 로거 객체
    
    Returns:
        Tuple[Optional[Image.Image], float, Optional[str]]: 
            (크롭된 이미지, YOLO 신뢰도, 에러 메시지)
            실패 시: (None, 0.0, 에러 메시지)
    """
    try:
        # YOLO 추론 (이미지당 하나의 박스만 검출: 가장 신뢰도가 높은 박스, CPU 모드)
        results = yolo_model(
            pil_image,
            verbose=False,
            conf=0.1,  # 낮은 임계값으로 후보 검출
            device='cpu',  # CPU 모드 강제
            max_det=1  # 최대 검출 개수: 1개 (가장 신뢰도 높은 박스만)
        )
        
        # 학번 영역 검출
        student_id_boxes = []
        detected_classes = set()
        all_boxes = []  # 모든 박스 정보 저장 (디버깅용)
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls)
                confidence = float(box.conf)
                detected_classes.add(class_id)
                
                xyxy = box.xyxy[0].tolist()
                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                
                all_boxes.append({
                    "class_id": class_id,
                    "confidence": confidence,
                    "bbox": (x1, y1, x2, y2)
                })
                
                # 학번 영역으로 간주 (이미 최고 신뢰도 박스 하나만 검출됨)
                if class_id == STUDENT_ID_CLASS_ID or confidence > 0.3:
                    student_id_boxes.append({
                        "bbox": (x1, y1, x2, y2),
                        "confidence": confidence,
                        "class_id": class_id
                    })
        
        # 디버깅: 검출된 클래스 및 박스 정보 로깅
        logger.info(f"YOLO detected {len(all_boxes)} box(es) total (max_det=1)")
        logger.info(f"Detected classes: {detected_classes}")
        if all_boxes:
            logger.info(f"Detected box: {all_boxes[0]}")
        logger.info(f"Student ID box (class_id={STUDENT_ID_CLASS_ID} or conf>0.3): {len(student_id_boxes)}")
        
        # 박스 검출 확인
        if len(student_id_boxes) == 0:
            logger.warning(f"No student ID area detected by YOLO in {image_file}")
            logger.warning(f"  - Total boxes detected: {len(all_boxes)}")
            logger.warning(f"  - Detected classes: {detected_classes}")
            error_msg = f"No student ID area detected (classes: {detected_classes}, boxes: {len(all_boxes)})"
            return None, 0.0, error_msg
        
        # 박스 선택 (이미 max_det=1로 하나만 검출됨)
        best_box = student_id_boxes[0] if student_id_boxes else None
        if best_box is None:
            raise Exception("No valid student ID box found")
        
        x1, y1, x2, y2 = best_box["bbox"]
        yolo_confidence = best_box["confidence"]
        detected_class_id = best_box.get("class_id", STUDENT_ID_CLASS_ID)
        logger.info(f"Selected box: class_id={detected_class_id}, confidence={yolo_confidence:.3f}, bbox=({x1},{y1},{x2},{y2})")
        
        # 학번 영역 크롭
        cropped_image = pil_image.crop((x1, y1, x2, y2))
        logger.debug(
            f"YOLO detected student ID area: bbox=({x1},{y1},{x2},{y2}), "
            f"conf={yolo_confidence:.3f}"
        )
        
        return cropped_image, yolo_confidence, None
    
    except Exception as e:
        logger.error(f"YOLO inference error for {image_file}: {e}")
        return None, 0.0, f"YOLO error: {str(e)}"

