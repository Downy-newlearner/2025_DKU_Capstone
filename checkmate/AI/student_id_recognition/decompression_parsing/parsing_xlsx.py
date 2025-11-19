import pandas as pd
import os
import re
import logging
from typing import List, Optional, Union

# 상수 정의
MAX_SEARCH_ROWS = 50  # 최대 헤더 탐색 행 수
MAX_SEARCH_COLS = 20  # 최대 헤더 탐색 열 수
MAX_EXTRACTION_ROWS = 10000  # 최대 추출 행 수 (성능 보호)

# 학번 헤더 키워드 (다양한 표현 지원)
STUDENT_ID_KEYWORDS = [
    "학번",
    "studentid",
    "student_id",
    "student id",
    "학생번호",
    "학생 번호"
]

# 학번 검증 정규식 (정확히 8자리 숫자)
STUDENT_ID_PATTERN = re.compile(r'^\d{8}$')


def normalize_cell_value(cell_value) -> str:
    """
    셀 값을 정규화합니다 (대소문자, 공백 처리).
    
    Args:
        cell_value: 셀의 원본 값
    
    Returns:
        str: 정규화된 문자열 (소문자, 공백 제거)
    """
    if cell_value is None:
        return ""
    
    # 문자열로 변환, 공백 제거, 소문자 변환
    normalized = str(cell_value).strip().lower()
    # 모든 공백 제거 (예: "학 번" -> "학번")
    normalized = re.sub(r'\s+', '', normalized)
    return normalized


def is_empty_cell(value) -> bool:
    """
    셀이 비어있는지 확인합니다.
    
    Args:
        value: 셀의 값
    
    Returns:
        bool: 비어있으면 True, 아니면 False
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized or normalized == 'nan':
            return True
        return False
    
    if isinstance(value, (int, float)):
        return pd.isna(value)
    
    return False


def is_valid_student_id(value) -> bool:
    """
    8자리 학번 검증을 수행합니다.
    
    Args:
        value: 검증할 값
    
    Returns:
        bool: 유효한 8자리 학번이면 True, 아니면 False
    """
    if value is None:
        return False
    
    str_value = str(value).strip()
    return bool(STUDENT_ID_PATTERN.match(str_value))


def matches_keyword(normalized: str, keyword: str) -> bool:
    """
    키워드가 정확히 매칭되는지 확인합니다.
    
    Args:
        normalized: 정규화된 셀 값
        keyword: 검색할 키워드
    
    Returns:
        bool: 매칭되면 True, 아니면 False
    """
    # 정확한 매칭
    if normalized == keyword:
        return True
    
    # 단어 경계 매칭 (예: "학번"이 독립된 단어로 존재)
    pattern = r'\b' + re.escape(keyword) + r'\b'
    return bool(re.search(pattern, normalized))


def parsing_xlsx(
    xlsx_file_path: Union[str, os.PathLike],
    logger: Optional[logging.Logger] = None
) -> List[str]:
    """
    XLSX 파일에서 학번 리스트를 추출합니다.
    
    "학번" 헤더를 찾아 해당 열의 아래 행들에서 8자리 숫자 학번을 추출합니다.
    
    Args:
        xlsx_file_path: XLSX 파일 경로
        logger: 로깅용 logger (None이면 기본 logger 생성)
    
    Returns:
        List[str]: 학번 문자열 리스트 (8자리 숫자). 추출 실패 시 빈 리스트 반환.
    
    Examples:
        >>> student_ids = parsing_xlsx("attendance.xlsx")
        >>> print(student_ids)
        ['32201959', '32202698', '32203946']
    """
    # ===== 단계 1: 로거 초기화 =====
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    # ===== 단계 2: 파일 검증 =====
    if not os.path.exists(xlsx_file_path):
        logger.error(f"XLSX file not found: {xlsx_file_path}")
        return []
    
    if not os.path.isfile(xlsx_file_path):
        logger.error(f"Path is not a file: {xlsx_file_path}")
        return []
    
    # ===== 단계 3: 파일 읽기 =====
    try:
        # dtype=str로 읽어서 앞의 0이 사라지지 않도록 함
        # na_filter=False로 NaN을 빈 문자열로 처리
        df = pd.read_excel(
            xlsx_file_path,
            header=None,
            engine='openpyxl',
            dtype=str,
            na_filter=False
        )
    except FileNotFoundError:
        logger.error(f"XLSX file not found: {xlsx_file_path}")
        return []
    except PermissionError:
        logger.error(f"Permission denied: {xlsx_file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading XLSX file {xlsx_file_path}: {e}", exc_info=True)
        return []
    
    # 빈 데이터프레임 확인
    if df.empty:
        logger.warning(f"XLSX file is empty: {xlsx_file_path}")
        return []
    
    # ===== 단계 4: "학번" 헤더 찾기 =====
    # 실제 사용된 열/행 수 확인 (동적 범위)
    actual_max_cols = min(MAX_SEARCH_COLS, len(df.columns))
    actual_max_rows = min(MAX_SEARCH_ROWS, len(df))
    
    header_row = None
    header_col = None
    
    # 1행부터 탐색 시작
    for row_idx in range(actual_max_rows):
        for col_idx in range(actual_max_cols):
            try:
                cell_value = df.iloc[row_idx, col_idx]
                normalized = normalize_cell_value(cell_value)
                
                # 키워드 매칭
                for keyword in STUDENT_ID_KEYWORDS:
                    if matches_keyword(normalized, keyword):
                        header_row = row_idx
                        header_col = col_idx
                        logger.info(
                            f"Found '학번' header at row {row_idx+1}, "
                            f"column {col_idx+1} (value: '{cell_value}')"
                        )
                        break
                
                if header_row is not None:
                    break
            
            except (IndexError, KeyError) as e:
                logger.debug(f"Error accessing cell [{row_idx}, {col_idx}]: {e}")
                continue
        
        if header_row is not None:
            break
    
    # 헤더를 찾지 못한 경우
    if header_row is None:
        logger.warning(
            f"Could not find '학번' header in first {actual_max_rows} rows, "
            f"{actual_max_cols} columns of {xlsx_file_path}"
        )
        return []
    
    # ===== 단계 5: 학번 추출 =====
    # 헤더 아래 행부터 시작
    start_row = header_row + 1
    student_numbers = []
    
    # 최대 추출 행 수 제한 (성능 보호)
    max_row = min(start_row + MAX_EXTRACTION_ROWS, len(df))
    
    # 각 행에서 학번 추출
    for row_idx in range(start_row, max_row):
        try:
            cell_value = df.iloc[row_idx, header_col]
            
            # 빈 셀 체크
            if is_empty_cell(cell_value):
                logger.debug(
                    f"Empty cell at row {row_idx+1}, column {header_col+1}. "
                    f"Stopping extraction."
                )
                break
            
            # 학번 검증 및 추가
            str_value = str(cell_value).strip()
            
            if is_valid_student_id(str_value):
                student_numbers.append(str_value)
                logger.debug(f"Extracted student ID at row {row_idx+1}: {str_value}")
            else:
                logger.debug(
                    f"Invalid student ID format at row {row_idx+1}, "
                    f"column {header_col+1}: '{str_value}'. Stopping extraction."
                )
                break
        
        except (IndexError, KeyError) as e:
            logger.warning(f"Error accessing cell [{row_idx}, {header_col}]: {e}")
            break
        except Exception as e:
            logger.warning(f"Unexpected error at row {row_idx+1}: {e}")
            continue
    
    # ===== 단계 6: 결과 정제 및 반환 =====
    # 중복 제거 (순서 유지)
    original_count = len(student_numbers)
    student_numbers = list(dict.fromkeys(student_numbers))
    duplicate_count = original_count - len(student_numbers)
    
    if duplicate_count > 0:
        logger.info(f"Removed {duplicate_count} duplicate student IDs")
    
    # 최종 결과 로깅
    if len(student_numbers) == 0:
        logger.warning(f"No student numbers extracted from {xlsx_file_path}")
    else:
        logger.info(
            f"Successfully extracted {len(student_numbers)} unique student numbers "
            f"from {xlsx_file_path}"
        )
    
    return student_numbers

