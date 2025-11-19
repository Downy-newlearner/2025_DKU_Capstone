"""
모델 로딩 및 관리 모듈
"""
import os
import logging
from typing import Optional
from ultralytics import YOLO
from paddleocr import PaddleOCR

from .config import YOLO_MODEL_PATH, OCR_LANG

# 전역 모델 변수 (재사용을 위해)
_yolo_model = None
_ocr_model = None


def get_yolo_model() -> Optional[YOLO]:
    """YOLO 모델 싱글톤 반환 (CPU 모드)"""
    global _yolo_model
    if _yolo_model is None:
        if os.path.exists(YOLO_MODEL_PATH):
            try:
                # CUDA 호환성 문제 해결: CPU 모드로 강제 설정
                if 'CUDA_VISIBLE_DEVICES' not in os.environ:
                    os.environ['CUDA_VISIBLE_DEVICES'] = ''
                _yolo_model = YOLO(YOLO_MODEL_PATH)
                # 모델을 CPU로 이동 (가능한 경우)
                try:
                    _yolo_model.to('cpu')
                except:
                    pass  # to() 메서드가 없을 수 있음
                logging.getLogger(__name__).info("YOLO model loaded in CPU mode")
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
            # 숫자만 인식하도록 설정
            _ocr_model = PaddleOCR(
                lang=OCR_LANG,  # 'en' 모델 사용 (숫자 인식에 적합)
                device='cpu',
                use_textline_orientation=False,
            )
        except Exception as e:
            logging.getLogger(__name__).error(f"Error initializing OCR model: {e}")
            return None
    return _ocr_model

