"""
이미지 처리 유틸리티 모듈
"""
import base64
import logging
import numpy as np
from io import BytesIO
from PIL import Image


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

