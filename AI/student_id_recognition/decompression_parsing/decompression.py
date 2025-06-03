import os
import zipfile
import tarfile
import shutil
import rarfile
from pathlib import Path

def extract_archive(archive_path: str, extract_path: str = None) -> bool:
    """
    다양한 형식의 압축 파일을 해제하는 함수
    
    Args:
        archive_path (str): 압축 파일의 경로
        extract_path (str, optional): 압축을 해제할 경로. 기본값은 압축 파일이 있는 디렉토리
        
    Returns:
        bool: 압축 해제 성공 여부
    """
    try:
        # 입력 경로를 Path 객체로 변환
        archive_path = Path(archive_path)
        
        # extract_path가 지정되지 않은 경우, 압축 파일 이름으로 새 폴더 생성
        if extract_path is None:
            folder_name = archive_path.stem  # 확장자를 제외한 파일명
            extract_path = archive_path.parent / folder_name
            
        # 압축 해제 폴더 생성
        os.makedirs(extract_path, exist_ok=True)
        print(f"압축 해제 폴더 생성: {extract_path}")
        
        # 압축 파일이 존재하는지 확인
        if not archive_path.exists():
            print(f"Error: File not found - {archive_path}")
            return False
            
        # 파일 확장자 확인
        extension = archive_path.suffix.lower()
        
        # ZIP 파일 처리
        if extension == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                # 모든 파일 목록 가져오기
                file_list = zip_ref.namelist()
                
                # __MACOSX 폴더와 ._ 로 시작하는 파일 제외
                file_list = [f for f in file_list if not ('__MACOSX' in f or os.path.basename(f).startswith('._'))]
                
                # 최상위 공통 디렉토리 찾기
                if file_list:
                    common_prefix = os.path.commonpath(file_list)
                    
                    # 파일 추출
                    for file in file_list:
                        try:
                            # 파일명 디코딩
                            try:
                                # CP437로 디코딩 후 UTF-8로 인코딩
                                decoded_name = file.encode('cp437').decode('utf-8')
                            except:
                                # 실패하면 원래 이름 사용
                                decoded_name = file
                            
                            # 공통 경로 제거하고 새 경로 생성
                            if common_prefix:
                                relative_path = decoded_name[len(common_prefix):].lstrip('/')
                            else:
                                relative_path = decoded_name
                            
                            # 빈 경로는 건너뛰기
                            if not relative_path:
                                continue
                            
                            target_path = os.path.join(extract_path, relative_path)
                            
                            # 디렉토리 생성
                            if decoded_name.endswith('/'):
                                os.makedirs(target_path, exist_ok=True)
                                continue
                            
                            # 파일 디렉토리 생성
                            os.makedirs(os.path.dirname(target_path), exist_ok=True)
                            
                            # 파일 추출
                            source = zip_ref.open(file)
                            with open(target_path, 'wb') as target:
                                shutil.copyfileobj(source, target)
                            
                        except Exception as e:
                            print(f"Warning: Failed to extract {file}: {str(e)}")
                            continue
                
        # TAR, TAR.GZ, TGZ 파일 처리
        elif extension in ['.tar', '.gz', '.tgz']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_path)
                
        # RAR 파일 처리
        elif extension == '.rar':
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_path)
                
        else:
            print(f"Error: Unsupported archive format - {extension}")
            return False
            
        print(f"Successfully extracted {archive_path} to {extract_path}")
        return True
        
    except Exception as e:
        print(f"Error extracting {archive_path}: {str(e)}")
        return False

if __name__ == "__main__":
    # 현재 작업 디렉토리에서 모든 zip 파일 찾기
    current_dir = Path.cwd()  # 현재 작업 디렉토리
    print(f"현재 디렉토리: {current_dir}")
    
    zip_files = list(current_dir.glob("*.zip"))
    
    if not zip_files:
        print("현재 디렉토리에 zip 파일이 없습니다.")
    else:
        print(f"발견된 zip 파일 개수: {len(zip_files)}")
        for zip_file in zip_files:
            print(f"\n압축 해제 중: {zip_file.name}")
            extract_archive(zip_file)
