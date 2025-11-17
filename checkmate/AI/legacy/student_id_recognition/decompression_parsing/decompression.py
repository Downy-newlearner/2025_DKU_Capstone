import zipfile
import os
import logging
import shutil
from pathlib import Path
from typing import Optional, Callable

# 기본 설정
BUFFER_SIZE = 8192  # 8KB 버퍼 (스트리밍용)
SUCCESS_THRESHOLD = 0.9  # 90% 이상 성공 시 성공으로 간주
ZIP_EXTRACTION_MULTIPLIER = 5  # 압축 해제 시 필요한 공간 배수 (안전 마진)


def extract_archive(
    zip_path: str,
    extracted_images_path: str,
    logger: Optional[logging.Logger] = None,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> bool:
    """
    ZIP 파일을 안전하게 압축 해제합니다.
    
    Args:
        zip_path: 압축 해제할 ZIP 파일 경로
        extracted_images_path: 압축 해제할 대상 디렉토리 경로
        logger: 로깅용 logger (None이면 기본 logger 생성)
        progress_callback: 진행 상황 콜백 함수 (current, total) -> None (선택적)
    
    Returns:
        bool: 성공 시 True, 실패 시 False
    """
    # 로거 초기화
    if logger is None:
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    # ===== 단계 1: 입력 검증 =====
    if not zip_path or not isinstance(zip_path, str):
        logger.error(f"Invalid zip_path: {zip_path}")
        return False
    
    if not extracted_images_path or not isinstance(extracted_images_path, str):
        logger.error(f"Invalid extracted_images_path: {extracted_images_path}")
        return False
    
    # ZIP 파일 존재 및 파일 타입 확인
    if not os.path.exists(zip_path):
        logger.error(f"ZIP file not found: {zip_path}")
        return False
    
    if not os.path.isfile(zip_path):
        logger.error(f"zip_path is not a file: {zip_path}")
        return False
    
    # ZIP 파일 형식 검증
    if not zipfile.is_zipfile(zip_path):
        logger.error(f"File is not a valid ZIP: {zip_path}")
        return False
    
    # ===== 단계 2: 디렉토리 생성 및 검증 =====
    try:
        os.makedirs(extracted_images_path, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create directory {extracted_images_path}: {e}")
        return False
    
    # 경로 정규화 (절대 경로로 변환)
    try:
        extracted_path_obj = Path(extracted_images_path).resolve()
        zip_path_obj = Path(zip_path).resolve()
    except (OSError, ValueError) as e:
        logger.error(f"Failed to resolve paths: {e}")
        return False
    
    # ===== 단계 3: 디스크 공간 확인 =====
    try:
        zip_size = os.path.getsize(zip_path)
        required_space = zip_size * ZIP_EXTRACTION_MULTIPLIER
        
        stat = shutil.disk_usage(extracted_path_obj)
        free_space = stat.free
        
        if free_space < required_space:
            logger.error(
                f"Insufficient disk space. Required: {required_space} bytes, "
                f"Available: {free_space} bytes"
            )
            return False
        
        logger.debug(
            f"Disk space check passed. Required: {required_space} bytes, "
            f"Available: {free_space} bytes"
        )
    except OSError as e:
        logger.warning(f"Could not check disk space: {e}. Proceeding anyway...")
    
    # ===== 단계 4: ZIP 파일 열기 및 압축 해제 =====
    extracted_count = 0
    failed_count = 0
    total_files = 0
    
    try:
        with zipfile.ZipFile(zip_path, 'r', allowZip64=True) as zip_ref:
            # ZIP 파일 무결성 테스트
            bad_file = zip_ref.testzip()
            if bad_file:
                logger.error(f"ZIP file is corrupted. Bad file: {bad_file}")
                return False
            
            # 파일 목록 가져오기
            members = zip_ref.namelist()
            total_files = len(members)
            
            if total_files == 0:
                logger.warning(f"ZIP file is empty: {zip_path}")
                return False
            
            logger.info(f"Starting extraction of {total_files} files from {zip_path}")
            
            # 개별 파일 추출 (경로 보안 검증 포함)
            for idx, member in enumerate(members):
                try:
                    # 진행 상황 콜백 호출
                    if progress_callback:
                        progress_callback(idx + 1, total_files)
                    
                    # 경로 보안 검증
                    member_path = os.path.normpath(member)
                    
                    # 경로 조작 방지: .. 또는 절대 경로 체크
                    if os.path.isabs(member_path) or '..' in member_path:
                        logger.warning(f"Skipping suspicious path in ZIP: {member}")
                        failed_count += 1
                        continue
                    
                    # 최종 추출 경로 생성
                    final_path_obj = (extracted_path_obj / member_path).resolve()
                    
                    # 경로가 여전히 extracted_path 밖으로 나가는지 재확인
                    try:
                        common = os.path.commonpath([extracted_path_obj, final_path_obj])
                        if common != str(extracted_path_obj):
                            logger.warning(
                                f"Path traversal detected: {member} -> {final_path_obj}"
                            )
                            failed_count += 1
                            continue
                    except ValueError:
                        # 경로가 공통되지 않음 (다른 드라이브 등)
                        logger.warning(
                            f"Path outside extraction directory: {member} -> {final_path_obj}"
                        )
                        failed_count += 1
                        continue
                    
                    # 디렉토리인 경우 생성
                    if member.endswith('/'):
                        try:
                            os.makedirs(final_path_obj, exist_ok=True)
                            extracted_count += 1
                        except OSError as e:
                            logger.error(f"Failed to create directory {final_path_obj}: {e}")
                            failed_count += 1
                            continue
                    else:
                        # 파일 추출 (스트리밍 방식)
                        try:
                            # 상위 디렉토리 생성
                            os.makedirs(final_path_obj.parent, exist_ok=True)
                            
                            # 스트리밍 방식으로 파일 추출
                            with zip_ref.open(member) as source:
                                with open(final_path_obj, 'wb') as target:
                                    while True:
                                        chunk = source.read(BUFFER_SIZE)
                                        if not chunk:
                                            break
                                        target.write(chunk)
                            
                            # 파일 권한 복원 (가능한 경우)
                            member_info = zip_ref.getinfo(member)
                            if member_info.external_attr:
                                try:
                                    os.chmod(final_path_obj, member_info.external_attr >> 16)
                                except (OSError, AttributeError):
                                    # Windows에서는 chmod가 제한적이므로 무시
                                    pass
                            
                            extracted_count += 1
                            
                        except PermissionError as e:
                            logger.error(
                                f"Permission denied extracting {member} to {final_path_obj}: {e}"
                            )
                            failed_count += 1
                            continue
                        except OSError as e:
                            logger.error(
                                f"OS error extracting {member} to {final_path_obj}: {e}"
                            )
                            failed_count += 1
                            continue
                        except MemoryError as e:
                            logger.error(f"Memory error extracting {member}: {e}")
                            failed_count += 1
                            continue
                        except Exception as e:
                            logger.error(
                                f"Unexpected error extracting {member}: {e}",
                                exc_info=True
                            )
                            failed_count += 1
                            continue
                
                except Exception as e:
                    logger.error(
                        f"Error processing member {member}: {e}",
                        exc_info=True
                    )
                    failed_count += 1
                    continue
    
    except zipfile.BadZipFile as e:
        logger.error(f"Bad ZIP file: {zip_path}. Error: {e}")
        return False
    except zipfile.LargeZipFile as e:
        logger.error(
            f"ZIP file requires ZIP64 extensions but not supported: {zip_path}. Error: {e}"
        )
        return False
    except PermissionError as e:
        logger.error(f"Permission denied accessing ZIP file {zip_path}: {e}")
        return False
    except OSError as e:
        logger.error(f"OS error accessing ZIP file {zip_path}: {e}")
        return False
    except MemoryError as e:
        logger.error(f"Memory error opening ZIP file {zip_path}: {e}")
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error opening ZIP file {zip_path}: {e}",
            exc_info=True
        )
        return False
    
    # ===== 단계 5: 결과 평가 =====
    if extracted_count == 0:
        logger.error(f"No files extracted from {zip_path}")
        return False
    
    # 성공률 계산
    success_rate = extracted_count / total_files if total_files > 0 else 0
    
    logger.info(
        f"Extraction completed: {extracted_count}/{total_files} files extracted "
        f"({success_rate*100:.1f}% success rate), {failed_count} failed"
    )
    
    # 성공률 임계값 확인
    if success_rate >= SUCCESS_THRESHOLD:
        logger.info(f"Extraction successful (success rate: {success_rate*100:.1f}%)")
        return True
    else:
        logger.warning(
            f"Extraction partially failed (success rate: {success_rate*100:.1f}% < "
            f"{SUCCESS_THRESHOLD*100}%)"
        )
        return False

