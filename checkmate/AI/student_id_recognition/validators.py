"""
검증 모듈
"""
import os
import logging
from typing import List, Tuple


def validate_inputs(
    extracted_images_path: str,
    subject_name: str,
    student_numbers_from_xlsx: List[str]
) -> Tuple[logging.Logger, List[str], bool]:
    """
    입력 파라미터 검증 및 로거 초기화.
    
    Args:
        extracted_images_path: 압축 해제된 이미지 폴더 경로
        subject_name: 과목명
        student_numbers_from_xlsx: XLSX에서 추출한 학번 리스트
    
    Returns:
        Tuple[logging.Logger, List[str], bool]: (로거, 검증된 학번 리스트, 성공 여부)
    """
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    # 입력 파라미터 검증
    if not os.path.exists(extracted_images_path):
        logger.error(f"Image directory not found: {extracted_images_path}")
        return logger, [], False
    
    if not os.path.isdir(extracted_images_path):
        logger.error(f"Path is not a directory: {extracted_images_path}")
        return logger, [], False
    
    if not subject_name:
        logger.error("subject_name is empty")
        return logger, [], False
    
    # student_numbers_from_xlsx 검증
    if not isinstance(student_numbers_from_xlsx, list):
        logger.warning("student_numbers_from_xlsx is not a list, converting to empty list")
        student_numbers_from_xlsx = []
    
    logger.info(f"Starting student ID recognition for subject: {subject_name}")
    logger.info(f"XLSX reference list contains {len(student_numbers_from_xlsx)} student IDs")
    
    return logger, student_numbers_from_xlsx, True

