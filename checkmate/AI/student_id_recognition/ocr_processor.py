"""
OCR 처리 모듈
"""
import os
import re
import logging
import numpy as np
from typing import Optional, Tuple
from PIL import Image
from paddleocr import PaddleOCR

from .config import STUDENT_ID_PATTERN
from .image_utils import preprocess_for_ocr


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


def recognize_student_id_with_ocr(
    ocr_model: PaddleOCR,
    cropped_image: Image.Image,
    image_file: str,
    logger: logging.Logger
) -> Tuple[Optional[str], float]:
    """
    OCR로 학번 인식.
    
    Args:
        ocr_model: PaddleOCR 모델 객체
        cropped_image: 크롭된 이미지
        image_file: 이미지 파일명 (로깅용)
        logger: 로거 객체
    
    Returns:
        Tuple[Optional[str], float]: (인식된 학번, OCR 신뢰도)
    """
    ocr_confidence = 0.0
    try:
        # OCR 전처리
        preprocessed_image = preprocess_for_ocr(cropped_image) # 대비 추가, 노이즈 제거
        
        # PIL Image를 numpy array로 변환
        cropped_array = np.array(preprocessed_image)
        
        # OCR 수행 (API 호환성 문제 해결)
        ocr_results = None
        try:
            # 최신 API 시도 (predict 메서드)
            if hasattr(ocr_model, 'predict'):
                ocr_results = ocr_model.predict(cropped_array)
            else:
                # 구버전 API (ocr 메서드)
                ocr_results = ocr_model.ocr(cropped_array)
        except (TypeError, AttributeError) as ocr_api_error:
            logger.debug(f"OCR failed: {ocr_api_error}, trying fallback")
            try:
                if hasattr(ocr_model, 'predict'):
                    ocr_results = ocr_model.predict(cropped_array)
                else:
                    ocr_results = ocr_model.ocr(cropped_array)
            except Exception as ocr_fallback_error:
                # 파일 경로로 시도
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    try:
                        cropped_image.save(tmp.name)
                        if hasattr(ocr_model, 'predict'):
                            ocr_results = ocr_model.predict(tmp.name)
                        else:
                            ocr_results = ocr_model.ocr(tmp.name)
                    finally:
                        try:
                            os.unlink(tmp.name)
                        except:
                            pass
        
        if ocr_results is None:
            raise Exception("OCR failed: All OCR methods failed")
        
        # OCR 결과 파싱
        recognized_text, ocr_confidence = parse_ocr_result(ocr_results)
        
        logger.debug(
            f"OCR result: '{recognized_text}', confidence: {ocr_confidence:.3f}"
        )
        
        # 8자리 학번 추출
        student_id_match = STUDENT_ID_PATTERN.search(recognized_text)
        if student_id_match:
            recognized_student_id = student_id_match.group()
            logger.info(
                f"Recognized student ID: {recognized_student_id} "
                f"from '{recognized_text}'"
            )
            return recognized_student_id, ocr_confidence
        else:
            logger.warning(
                f"8-digit student ID not found in OCR result: '{recognized_text}'"
            )
            return None, ocr_confidence
    
    except Exception as e:
        logger.error(f"OCR error for {image_file}: {e}")
        return None, 0.0

