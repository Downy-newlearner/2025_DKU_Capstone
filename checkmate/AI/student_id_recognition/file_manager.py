"""
파일 관리 모듈
"""
import os
import json
import logging
from typing import List, Dict, Any

from .config import IMAGE_EXTENSIONS


def collect_image_files(extracted_images_path: str, logger: logging.Logger) -> List[str]:
    """
    이미지 디렉토리에서 이미지 파일 목록 수집.
    
    Args:
        extracted_images_path: 이미지 디렉토리 경로
        logger: 로거 객체
    
    Returns:
        List[str]: 이미지 파일명 리스트 (정렬됨)
    """
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
        
        return image_files
    
    except OSError as e:
        logger.error(f"Error listing directory: {e}")
        return []


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


def save_results(
    result: Dict[str, Any],
    extracted_images_path: str,
    logger: logging.Logger
) -> None:
    """
    결과를 JSON 파일로 저장.
    
    Args:
        result: 결과 딕셔너리
        extracted_images_path: 이미지 디렉토리 경로
        logger: 로거 객체
    """
    debug_json_path = os.path.join(extracted_images_path, "student_id_recognition_debug.json")
    try:
        with open(debug_json_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.debug(f"Debug JSON saved: {debug_json_path}")
    except Exception as e:
        logger.warning(f"Failed to save debug JSON: {e}")

