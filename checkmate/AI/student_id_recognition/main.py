"""
학번 인식 메인 모듈

YOLO 모델로 학번 영역을 검출하고, OCR로 학번을 인식합니다.
신뢰도가 낮은 이미지는 Base64 인코딩하여 반환합니다.
"""
import os
import gc
from typing import List, Dict, Any, Optional
from PIL import Image

# 모듈 import
from . import config
from .models import get_yolo_model, get_ocr_model
from .validators import validate_inputs
from .file_manager import collect_image_files, save_results
from .yolo_detector import detect_student_id_area
from .ocr_processor import recognize_student_id_with_ocr
from .result_handler import handle_processing_result
from .kafka_client import send_kafka_status, KafkaProducer
from .image_utils import image_to_base64_fallback, image_to_base64


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
    # CUDA 비활성화 (CPU 모드로 강제 실행 - 호환성 문제 해결)
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # ===== 단계 1: 초기화 및 검증 =====
    logger, student_numbers_from_xlsx, is_valid = validate_inputs(
        extracted_images_path, subject_name, student_numbers_from_xlsx
    )
    if not is_valid:
        return {"subject": subject_name, "lowConfidenceImages": []}
    
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
    image_files = collect_image_files(extracted_images_path, logger)
    if not image_files:
        logger.warning("No image files found")
        return {"subject": subject_name, "lowConfidenceImages": []}
    
    total_images = len(image_files)
    
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
                    pil_image = original_image.copy()
            except Exception as e:
                logger.error(f"Error reading image {image_file}: {e}")
                failed_count += 1
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": image_to_base64_fallback(image_path),
                    "error": f"Image read error: {str(e)}"
                })
                continue
            
            # 4-2. YOLO로 학번 영역 검출
            cropped_image, yolo_confidence, yolo_error = detect_student_id_area(
                yolo_model, pil_image, image_file, logger
            )
            
            if yolo_error is not None:
                # YOLO 검출 실패
                failed_count += 1
                low_confidence_images.append({
                    "file_name": image_file,
                    "base64_data": image_to_base64(pil_image),
                    "error": yolo_error
                })
                del pil_image
                continue
            
            # 4-3. OCR로 학번 인식
            # recognized_student_id가 None이면 신뢰도 0.0으로 설정
            recognized_student_id, ocr_confidence = recognize_student_id_with_ocr(
                ocr_model, cropped_image, image_file, logger
            )
            
            # 4-4. 최종 신뢰도 계산 (OCR 신뢰도 사용)
            if recognized_student_id:
                final_confidence = ocr_confidence
            else:
                final_confidence = 0.0
            
            # 4-5. XLSX 리스트 검증 (선택적)
            if recognized_student_id and student_numbers_from_xlsx:
                if recognized_student_id not in student_numbers_from_xlsx:
                    logger.warning(
                        f"Recognized student ID {recognized_student_id} not in XLSX list. "
                        f"Lowering confidence."
                    )
                    final_confidence = min(final_confidence, 0.7)
            
            # 4-6. 신뢰도 평가 및 처리
            # OCR 신뢰도가 0.8보다 낮으면 is_success를 False로 설정하고, low_confidence_images에 추가(Base64 인코딩 이미지 추가)
            is_success, low_confidence_images = handle_processing_result(
                recognized_student_id,
                final_confidence,
                image_file,
                image_path,
                pil_image,
                subject_name,
                extracted_images_path,
                low_confidence_images,
                logger
            )
            
            if is_success:
                success_count += 1
            else:
                failed_count += 1
            
            processed_count += 1
            
            # 메모리 정리
            del pil_image
            if cropped_image:
                del cropped_image
            
            # 주기적 가비지 컬렉션
            if (idx + 1) % 50 == 0:
                gc.collect()
            
            # 4-7. Kafka 진행 상황 전송 (선택적)
            if (idx + 1) % 10 == 0:  # 10개마다 전송
                send_kafka_status(
                    producer,
                    student_id_recognition_topic,
                    status="PENDING"
                )
        
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
    
    # JSON 파일 저장
    save_results(result, extracted_images_path, logger)
    
    # 최종 Kafka 상태 전송
    send_kafka_status(
        producer,
        student_id_recognition_topic,
        status="DONE",
        low_confidence_images=low_confidence_images
    )
    
    return result
