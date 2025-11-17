import os
import re
import base64
import logging
import json
import gc
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from io import BytesIO
from PIL import Image
import numpy as np
from ultralytics import YOLO
from paddleocr import PaddleOCR

# Kafka는 선택적 import
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    # KafkaProducer가 없을 경우를 위한 타입 힌트
    KafkaProducer = type(None)

# ===== 상수 정의 =====
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
YOLO_MODEL_PATH = os.path.join(MODEL_DIR, 'best_student_id.pt')

# YOLO 설정
STUDENT_ID_CLASS_ID = 0  # 학번 영역 클래스 ID (args_student_id.yaml 확인 필요)
YOLO_CONF_THRESHOLD = 0.25  # YOLO 신뢰도 임계값 (args_student_id.yaml: conf: 0.22)

# OCR 설정
OCR_USE_GPU = False  # 또는 True
OCR_LANG = 'en'  # 숫자만 인식 (영어 모델이 숫자 인식에 적합)

# 신뢰도 설정
CONFIDENCE_THRESHOLD = 0.8  # 최종 신뢰도 임계값
YOLO_WEIGHT = 0.6  # YOLO 신뢰도 가중치
OCR_WEIGHT = 0.4  # OCR 신뢰도 가중치

# 이미지 파일 확장자
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# 학번 정규식
STUDENT_ID_PATTERN = re.compile(r'\d{8}')

# 전역 모델 변수 (재사용을 위해)
_yolo_model = None
_ocr_model = None


def get_yolo_model() -> Optional[YOLO]:
    """YOLO 모델 싱글톤 반환"""
    global _yolo_model
    if _yolo_model is None:
        if os.path.exists(YOLO_MODEL_PATH):
            try:
                _yolo_model = YOLO(YOLO_MODEL_PATH)
            except Exception as e:
                logging.getLogger(__name__).error(f"Error loading YOLO model: {e}")
                return None
        else:
            logging.getLogger(__name__).error(f"YOLO model not found: {YOLO_MODEL_PATH}")
            return None
    return _yolo_model


def get_ocr_model() -> Optional[PaddleOCR]:
    """OCR 모델 싱글톤 반환 (숫자만 인식)"""
    global _ocr_model
    if _ocr_model is None:
        try:
            # 숫자만 인식하도록 설정 (최소한의 인자만 사용)
            # PaddleOCR 버전에 따라 인자 이름이 다를 수 있으므로 기본값 사용
            _ocr_model = PaddleOCR(
                lang=OCR_LANG,  # 'en' 모델 사용 (숫자 인식에 적합)
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Error initializing OCR model: {e}")
            return None
    return _ocr_model


def image_to_base64(image: Image.Image) -> str:
    """
    PIL Image를 Base64 문자열로 변환합니다.
    
    Args:
        image: PIL Image 객체
    
    Returns:
        str: Base64 인코딩된 문자열 (접두사 없음)
    """
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=85)
    img_bytes = buffered.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64


def image_to_base64_fallback(image_path: str) -> str:
    """
    이미지 파일 경로에서 Base64로 변환합니다 (fallback).
    
    Args:
        image_path: 이미지 파일 경로
    
    Returns:
        str: Base64 인코딩된 문자열
    """
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
    except Exception as e:
        logging.getLogger(__name__).error(f"Error encoding image to base64: {e}")
        return ""


def preprocess_for_ocr(image: Image.Image) -> Image.Image:
    """
    OCR을 위한 이미지 전처리 (대비 향상, 노이즈 제거).
    
    Args:
        image: PIL Image 객체
    
    Returns:
        Image.Image: 전처리된 PIL Image 객체
    """
    try:
        import cv2
        
        # PIL → numpy array
        img_array = np.array(image)
        
        # 그레이스케일 변환
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        # 대비 향상 (CLAHE)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # 노이즈 제거
        denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
        
        # numpy array → PIL
        return Image.fromarray(denoised)
    
    except Exception as e:
        logging.getLogger(__name__).warning(f"OCR preprocessing failed: {e}. Using original image.")
        return image


def parse_ocr_result(ocr_results) -> Tuple[str, float]:
    """
    OCR 결과에서 숫자만 추출하고 신뢰도를 계산합니다.
    
    Args:
        ocr_results: PaddleOCR 결과
    
    Returns:
        Tuple[str, float]: (인식된 숫자 텍스트, 평균 신뢰도)
    """
    recognized_text = ""
    confidences = []
    
    if not ocr_results:
        return "", 0.0
    
    try:
        # PaddleOCR 결과 형식: [[[좌표], (텍스트, 신뢰도)], ...]
        for line_result in ocr_results:
            if isinstance(line_result, list) and len(line_result) >= 2:
                text_info = line_result[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = str(text_info[0])
                    conf = float(text_info[1])
                    # 숫자만 추출
                    digits_only = re.sub(r'[^\d]', '', text)
                    if digits_only:
                        recognized_text += digits_only
                        confidences.append(conf)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error parsing OCR result: {e}")
    
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    return recognized_text, avg_confidence


def calculate_confidence(yolo_conf: float, ocr_conf: float, method: str = "weighted") -> float:
    """
    YOLO와 OCR 신뢰도를 결합하여 최종 신뢰도를 계산합니다.
    
    Args:
        yolo_conf: YOLO 검출 신뢰도
        ocr_conf: OCR 인식 신뢰도
        method: 결합 방법 ("weighted", "product", "min", "max", "average")
    
    Returns:
        float: 최종 신뢰도
    """
    if method == "weighted":
        return YOLO_WEIGHT * yolo_conf + OCR_WEIGHT * ocr_conf
    elif method == "product":
        return yolo_conf * ocr_conf
    elif method == "min":
        return min(yolo_conf, ocr_conf)
    elif method == "max":
        return max(yolo_conf, ocr_conf)
    else:  # "average"
        return (yolo_conf + ocr_conf) / 2


def get_unique_filename(base_path: str, desired_filename: str) -> str:
    """
    고유한 파일명을 생성합니다 (충돌 시 번호 추가).
    
    Args:
        base_path: 기본 경로
        desired_filename: 원하는 파일명
    
    Returns:
        str: 고유한 파일명
    """
    if not os.path.exists(os.path.join(base_path, desired_filename)):
        return desired_filename
    
    name, ext = os.path.splitext(desired_filename)
    counter = 1
    while True:
        new_filename = f"{name}_{counter}{ext}"
        if not os.path.exists(os.path.join(base_path, new_filename)):
            return new_filename
        counter += 1
        if counter > 1000:  # 무한 루프 방지
            import uuid
            return f"{name}_{uuid.uuid4().hex[:8]}{ext}"


def main(
    extracted_images_path: str,
    student_numbers_from_xlsx: List[str],
    subject_name: str,
    producer: Optional[KafkaProducer],
    student_id_recognition_topic: str,
    task_identifier: str
) -> Dict[str, Any]:
    """
    학번 인식 메인 함수.
    
    YOLO 모델로 학번 영역을 검출하고, OCR로 학번을 인식합니다.
    신뢰도가 낮은 이미지는 Base64 인코딩하여 반환합니다.
    
    Args:
        extracted_images_path: 압축 해제된 이미지 폴더 경로
        student_numbers_from_xlsx: XLSX에서 추출한 학번 리스트 (참조용)
        subject_name: 과목명
        producer: Kafka Producer 객체 (None 가능)
        student_id_recognition_topic: Kafka 토픽명
        task_identifier: 작업 식별자
    
    Returns:
        Dict[str, Any]: 다음 키를 포함하는 딕셔너리
            - "subject": str (과목명)
            - "lowConfidenceImages": List[dict] (낮은 신뢰도 이미지 정보)
    """
    # ===== 단계 1: 초기화 및 검증 =====
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # 입력 파라미터 검증
    if not os.path.exists(extracted_images_path):
        logger.error(f"Image directory not found: {extracted_images_path}")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    if not os.path.isdir(extracted_images_path):
        logger.error(f"Path is not a directory: {extracted_images_path}")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    if not subject_name:
        logger.error("subject_name is empty")
        return {"subject": "", "lowConfidenceImages": []}
    
    # student_numbers_from_xlsx 검증
    if not isinstance(student_numbers_from_xlsx, list):
        logger.warning("student_numbers_from_xlsx is not a list, converting to empty list")
        student_numbers_from_xlsx = []
    
    logger.info(f"Starting student ID recognition for subject: {subject_name}")
    logger.info(f"XLSX reference list contains {len(student_numbers_from_xlsx)} student IDs")
    
    # ===== 단계 2: 모델 로드 =====
    yolo_model = get_yolo_model()
    if yolo_model is None:
        logger.error("Failed to load YOLO model")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    ocr_model = get_ocr_model()
    if ocr_model is None:
        logger.error("Failed to initialize OCR model")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    logger.info("Models loaded successfully")
    
    # ===== 단계 3: 이미지 파일 목록 수집 =====
    image_files = []
    try:
        for filename in os.listdir(extracted_images_path):
            file_path = os.path.join(extracted_images_path, filename)
            if os.path.isfile(file_path):
                ext = os.path.splitext(filename)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    image_files.append(filename)
        
        # 파일명 정렬
        image_files.sort()
        
        total_images = len(image_files)
        logger.info(f"Found {total_images} image files in {extracted_images_path}")
        
        if total_images == 0:
            logger.warning("No image files found")
            return {"subject": subject_name, "lowConfidenceImages": []}
    
    except OSError as e:
        logger.error(f"Error listing directory: {e}")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    # ===== 단계 4: 각 이미지 처리 (메인 루프) =====
    low_confidence_images = []
    processed_count = 0
    success_count = 0
    failed_count = 0
    
    for idx, image_file in enumerate(image_files):
        image_path = os.path.join(extracted_images_path, image_file)
        
        try:
            logger.info(f"Processing [{idx+1}/{total_images}]: {image_file}")
            
            # 4-1. 이미지 읽기
            try:
                with Image.open(image_path) as original_image:
                    # RGB로 변환
                    if original_image.mode != 'RGB':
                        original_image = original_image.convert('RGB')
                    
                    # 이미지 복사 (원본 보존)
                    pil_image = original_image.copy()
            except Exception as e:
                logger.error(f"Error reading image {image_file}: {e}")
                failed_count += 1
                # 읽기 실패 시 낮은 신뢰도로 처리
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": image_to_base64_fallback(image_path),
                    "error": f"Image read error: {str(e)}"
                })
                continue
            
            # 4-2. YOLO 추론 수행
            recognized_student_id = None
            yolo_confidence = 0.0
            cropped_image = None
            
            try:
                # YOLO 추론 (신뢰도 임계값을 낮춰서 더 많은 박스 검출)
                results = yolo_model(pil_image, verbose=False, conf=0.1)  # 임계값 낮춤
                
                # 4-3. 학번 영역 검출
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
                        
                        # 모든 클래스 ID를 시도 (클래스 ID가 0이 아닐 수 있음)
                        # 또는 신뢰도가 높은 박스를 학번으로 간주
                        if class_id == STUDENT_ID_CLASS_ID or confidence > 0.3:
                            student_id_boxes.append({
                                "bbox": (x1, y1, x2, y2),
                                "confidence": confidence,
                                "class_id": class_id
                            })
                
                # 디버깅: 검출된 클래스 및 박스 정보 로깅
                logger.info(f"YOLO detected {len(all_boxes)} boxes total")
                logger.info(f"Detected classes: {detected_classes}")
                if all_boxes:
                    logger.info(f"All boxes: {all_boxes[:5]}")  # 처음 5개만 출력
                logger.info(f"Student ID boxes (class_id={STUDENT_ID_CLASS_ID} or conf>0.3): {len(student_id_boxes)}")
                
                # 4-4. 여러 박스 처리: 최고 신뢰도 선택
                if len(student_id_boxes) == 0:
                    logger.warning(f"No student ID area detected by YOLO in {image_file}")
                    logger.warning(f"  - Total boxes detected: {len(all_boxes)}")
                    logger.warning(f"  - Detected classes: {detected_classes}")
                    # 학번 영역 미검출 → 낮은 신뢰도 처리
                    low_confidence_images.append({
                        "file_name": image_file,
                        "base64_data": image_to_base64(pil_image),
                        "error": f"No student ID area detected (classes: {detected_classes}, boxes: {len(all_boxes)})"
                    })
                    failed_count += 1
                    del pil_image
                    continue
                
                # 최고 신뢰도 박스 선택
                best_box = max(student_id_boxes, key=lambda x: x["confidence"])
                x1, y1, x2, y2 = best_box["bbox"]
                yolo_confidence = best_box["confidence"]
                detected_class_id = best_box.get("class_id", STUDENT_ID_CLASS_ID)
                logger.info(f"Selected box: class_id={detected_class_id}, confidence={yolo_confidence:.3f}, bbox=({x1},{y1},{x2},{y2})")
                
                # 4-5. 학번 영역 크롭
                cropped_image = pil_image.crop((x1, y1, x2, y2))
                logger.debug(
                    f"YOLO detected student ID area: bbox=({x1},{y1},{x2},{y2}), "
                    f"conf={yolo_confidence:.3f}"
                )
            
            except Exception as e:
                logger.error(f"YOLO inference error for {image_file}: {e}")
                failed_count += 1
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": image_to_base64(pil_image),
                    "error": f"YOLO error: {str(e)}"
                })
                del pil_image
                continue
            
            # 4-6. OCR로 학번 인식
            ocr_confidence = 0.0
            try:
                # OCR 전처리
                preprocessed_image = preprocess_for_ocr(cropped_image)
                
                # PIL Image를 numpy array로 변환
                cropped_array = np.array(preprocessed_image)
                
                # OCR 수행
                ocr_results = ocr_model.ocr(cropped_array, cls=True)
                
                # OCR 결과 파싱
                recognized_text, ocr_confidence = parse_ocr_result(ocr_results)
                
                logger.debug(
                    f"OCR result: '{recognized_text}', confidence: {ocr_confidence:.3f}"
                )
                
                # 4-7. 8자리 학번 추출
                student_id_match = STUDENT_ID_PATTERN.search(recognized_text)
                if student_id_match:
                    recognized_student_id = student_id_match.group()
                    logger.info(
                        f"Recognized student ID: {recognized_student_id} "
                        f"from '{recognized_text}'"
                    )
                else:
                    logger.warning(
                        f"8-digit student ID not found in OCR result: '{recognized_text}'"
                    )
                    recognized_student_id = None
            
            except Exception as e:
                logger.error(f"OCR error for {image_file}: {e}")
                ocr_confidence = 0.0
            
            # 4-8. 최종 신뢰도 계산
            if recognized_student_id:
                # 가중 평균
                final_confidence = calculate_confidence(
                    yolo_confidence, ocr_confidence, method="weighted"
                )
            else:
                # 학번 추출 실패 → 신뢰도 0
                final_confidence = 0.0
            
            # 4-9. XLSX 리스트 검증 (선택적)
            if recognized_student_id and student_numbers_from_xlsx:
                if recognized_student_id not in student_numbers_from_xlsx:
                    logger.warning(
                        f"Recognized student ID {recognized_student_id} not in XLSX list. "
                        f"Lowering confidence."
                    )
                    # 리스트에 없으면 신뢰도 낮춤
                    final_confidence = min(final_confidence, 0.7)
            
            # 4-10. 신뢰도 평가 및 처리
            if final_confidence < CONFIDENCE_THRESHOLD or not recognized_student_id:
                # 낮은 신뢰도 → Base64 인코딩 및 리스트 추가
                base64_data = image_to_base64(pil_image)
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": base64_data
                })
                logger.info(
                    f"Low confidence ({final_confidence:.3f}): {image_file}, "
                    f"recognized: {recognized_student_id or 'None'}"
                )
                failed_count += 1
            else:
                # 높은 신뢰도 → 파일명 변경 (선택적)
                try:
                    new_filename = f"{subject_name}_{recognized_student_id}.jpg"
                    new_filename = get_unique_filename(extracted_images_path, new_filename)
                    new_path = os.path.join(extracted_images_path, new_filename)
                    
                    # 파일명이 다를 경우만 변경
                    if image_file != new_filename:
                        os.rename(image_path, new_path)
                        logger.info(f"Renamed: {image_file} -> {new_filename}")
                except OSError as e:
                    logger.warning(f"Failed to rename {image_file}: {e}")
                    # 파일명 변경 실패해도 계속 진행
                
                success_count += 1
                logger.info(
                    f"Success ({final_confidence:.3f}): {image_file} -> "
                    f"{recognized_student_id}"
                )
            
            processed_count += 1
            
            # 메모리 정리
            del pil_image
            if cropped_image:
                del cropped_image
            
            # 주기적 가비지 컬렉션
            if (idx + 1) % 50 == 0:
                gc.collect()
            
            # 4-11. Kafka 진행 상황 전송 (선택적)
            if producer and KAFKA_AVAILABLE and (idx + 1) % 10 == 0:  # 10개마다 전송
                try:
                    progress_msg = {
                        "task_id": task_identifier,
                        "status": "processing",
                        "current": idx + 1,
                        "total": total_images,
                        "subject": subject_name,
                        "success": success_count,
                        "failed": failed_count
                    }
                    producer.send(student_id_recognition_topic, progress_msg)
                except Exception as e:
                    logger.warning(f"Kafka progress send failed: {e}")
        
        except Exception as e:
            logger.error(
                f"Unexpected error processing {image_file}: {e}",
                exc_info=True
            )
            failed_count += 1
            # 예외 발생 시 낮은 신뢰도로 처리
            try:
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": image_to_base64_fallback(image_path),
                    "error": f"Unexpected error: {str(e)}"
                })
            except:
                pass
            continue
    
    # ===== 단계 5: 결과 반환 =====
    # 최종 통계 로깅
    logger.info(
        f"Processing completed: {processed_count}/{total_images} processed, "
        f"{success_count} success, {failed_count} failed, "
        f"{len(low_confidence_images)} low confidence"
    )
    
    # 결과 딕셔너리 생성
    result = {
        "subject": subject_name,
        "lowConfidenceImages": low_confidence_images
    }
    
    # JSON 파일 저장 (선택적, 디버깅용)
    debug_json_path = os.path.join(extracted_images_path, "student_id_recognition_debug.json")
    try:
        with open(debug_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.debug(f"Debug JSON saved: {debug_json_path}")
    except Exception as e:
        logger.warning(f"Failed to save debug JSON: {e}")
    
    # 최종 Kafka 진행 상황 전송
    if producer and KAFKA_AVAILABLE:
        try:
            final_progress_msg = {
                "task_id": task_identifier,
                "status": "completed",
                "total": total_images,
                "success": success_count,
                "failed": failed_count,
                "low_confidence_count": len(low_confidence_images),
                "subject": subject_name
            }
            producer.send(student_id_recognition_topic, final_progress_msg)
            producer.flush()
        except Exception as e:
            logger.warning(f"Kafka final progress send failed: {e}")
    
    return result

