"""
결과 처리 모듈
"""
import os
import logging
from typing import List, Dict, Optional, Tuple

from .config import CONFIDENCE_THRESHOLD
from .image_utils import image_to_base64
from .file_manager import get_unique_filename


def handle_processing_result(
    recognized_student_id: Optional[str],
    final_confidence: float,
    image_file: str,
    image_path: str,
    pil_image,
    subject_name: str,
    extracted_images_path: str,
    low_confidence_images: List[Dict],
    logger: logging.Logger
) -> Tuple[bool, List[Dict]]:
    """
    처리 결과에 따라 파일명 변경 또는 낮은 신뢰도 처리.
    
    Args:
        recognized_student_id: 인식된 학번
        final_confidence: 최종 신뢰도
        image_file: 원본 이미지 파일명
        image_path: 이미지 파일 경로
        pil_image: PIL Image 객체
        subject_name: 과목명
        extracted_images_path: 이미지 디렉토리 경로
        low_confidence_images: 낮은 신뢰도 이미지 리스트
        logger: 로거 객체
    
    Returns:
        Tuple[bool, List[Dict]]: (성공 여부, 업데이트된 낮은 신뢰도 이미지 리스트)
    """
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
        return False, low_confidence_images
    else:
        # 높은 신뢰도 → 파일명 변경
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
        
        logger.info(
            f"Success ({final_confidence:.3f}): {image_file} -> "
            f"{recognized_student_id}"
        )
        return True, low_confidence_images

