import json
from .student_num_comparision.student_num_comparision import student_num_comparision
from .extract_student_num.extract_student_num import extract_student_num
from .decompression_parsing.parsing_xlsx import parsing_xlsx
from .decompression_parsing.decompression import extract_archive
import os
import shutil
from pathlib import Path
from pymongo import MongoClient
from bson import ObjectId
import base64

client = MongoClient('mongodb://localhost:27017')  # 연결 정보에 맞게 수정
db = client['capstone']
collection = db['exams']


def make_json(processed_dir_path):
    # 디렉토리명(과목명) 추출
    subject = os.path.basename(os.path.normpath(processed_dir_path))
    # JSON 구조 생성
    data = {
        "subject": subject,
        "images": []  # 키 변경 및 초기화
    }

    # 처리할 이미지 파일 확장자 정의
    allowed_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

    try:
        for filename in os.listdir(processed_dir_path):
            if filename.lower().endswith(allowed_extensions):
                file_path = os.path.join(processed_dir_path, filename)
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "rb") as image_file:
                            # 이미지를 base64로 인코딩하고 utf-8 문자열로 디코딩
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        
                        data["images"].append({
                            "file_name": filename,
                            "base64_data": encoded_string
                        })
                    except Exception as e:
                        # 개별 파일 처리 중 오류 발생 시 로그 (실제 환경에서는 logging 모듈 사용 권장)
                        print(f"Error processing file {file_path}: {e}")
    except FileNotFoundError:
        print(f"Error: Directory not found at {processed_dir_path}")
        # 필요시 data 딕셔너리에 오류 정보 추가 가능
        # data["error"] = f"Directory not found: {processed_dir_path}"
    except PermissionError:
        print(f"Error: Permission denied for directory {processed_dir_path}")
        # data["error"] = f"Permission denied: {processed_dir_path}"
    except Exception as e:
        # 기타 디렉토리 접근 오류 처리
        print(f"An unexpected error occurred while accessing directory {processed_dir_path}: {e}")
        # data["error"] = f"Unexpected error: {str(e)}"

    return data

# 메인 처리 함수
def main(answer_sheet_dir_path: str, student_id_list: list) -> dict:
    """
    지정된 디렉토리 내의 답안지 이미지들에서 학번을 인식하고,
    학적부의 학번 리스트와 비교하여 파일명을 변경하거나 특정 JSON 구조에 추가합니다.

    Args:
        answer_sheet_dir_path (str): (압축 해제된) 답안지 이미지들이 있는 디렉토리 경로.
        student_id_list (list): 학적부에서 파싱된 학번 문자열 리스트.

    Returns:
        dict: 처리 결과를 담은 딕셔너리. JSON 형식은 다음과 같습니다:
              {
                  "subject": "과목명(디렉토리명 기반)",
                  "base64_data": ["해당_학번영역_크롭이미지_base64_문자열1", ...]
              }
              - "base64_data"는 인식에 실패했거나 학적부와 일치하지 않아
                파일명 변경이 되지 않은 경우에만 데이터가 추가됩니다.
    """
    actual_answer_sheet_dir = answer_sheet_dir_path
    result_json = make_json(actual_answer_sheet_dir)

    for root, dirs, files in os.walk(actual_answer_sheet_dir):
        # __MACOSX 폴더 자체를 탐색에서 제외
        if '__MACOSX' in dirs:
            dirs.remove('__MACOSX')
        
        for file in files:
            if file.startswith('._') or '__MACOSX' in root: # ._로 시작하는 숨김 파일 및 __MACOSX 내부 파일 건너뛰기
                continue

            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            answer_sheet = os.path.join(root, file)
            student_num, cropped_stduend_ID_image_base64_data = extract_student_num(answer_sheet) 
            print(f"DEBUG: Processing {file}, extracted student_num: {student_num}")
            
            print(f"DEBUG: Base64 data is None: {cropped_stduend_ID_image_base64_data is None}")
            if cropped_stduend_ID_image_base64_data:
                print(f"DEBUG: Base64 data length: {len(cropped_stduend_ID_image_base64_data)}")
                print(f"DEBUG: Base64 data preview: {cropped_stduend_ID_image_base64_data[:50]}...")
            
            go_to_json = student_num_comparision(student_num, student_id_list)
            print(f"DEBUG: For {file}, student_num_comparision returned: {go_to_json}")
            
            if go_to_json:
                result_json['images'].append({
                    "file_name": file,
                    "base64_data": cropped_stduend_ID_image_base64_data
                })
                print(f"DEBUG: Added base64 data to list. Current list length: {len(result_json['images'])}")
                continue
            
            else: 
                if student_num: 
                    base, ext = os.path.splitext(file)
                    new_file_name = f"{student_num}{ext if ext else '.jpg'}" 
                    new_file_path = os.path.join(root, new_file_name)
                    
                    if os.path.exists(new_file_path):
                        print(f"경고: 파일명 변경 시 중복 발생 ({new_file_path}). 원본 파일명 유지: {file}")
                    else:
                        try:
                            os.rename(answer_sheet, new_file_path)
                            print(f"파일명 변경: {answer_sheet} -> {new_file_path}")
                        except Exception as e:
                            print(f"파일명 변경 실패 {answer_sheet}: {e}")       
                else:
                    print(f"학번 추출 실패(None)했으나 파일명 변경 로직 진입 (예상치 못한 상황): {answer_sheet}")
    
    return result_json

# 예시 실행 코드
if __name__ == '__main__':
    # --- 설정 ---
    base_dir = "/home/jdh251425/2025_DKU_Capstone-AI-2/AI/test_data"
    test_zip_file_path = os.path.join(base_dir, "test_answer.zip")
    test_xlsx_file_path = os.path.join(base_dir, "학적정보.xlsx")
    
    extracted_images_dir = os.path.join(base_dir, Path(test_zip_file_path).stem)

    # print(f"--- 테스트 준비 ---") # 주석 처리
    # print(f"입력 ZIP 파일: {test_zip_file_path}") # 주석 처리
    # print(f"학적 정보 XLSX 파일: {test_xlsx_file_path}") # 주석 처리
    # print(f"압축 해제 목표 디렉토리: {extracted_images_dir}") # 주석 처리

    # --- 1. 압축 해제 ---
    # print(f"\n--- 1. 압축 해제 시작 ---") # 주석 처리
    if os.path.exists(test_zip_file_path):
        if os.path.exists(extracted_images_dir):
            # print(f"기존 압축 해제 폴더 {extracted_images_dir} 삭제 중...") # 주석 처리
            shutil.rmtree(extracted_images_dir)

        extraction_success = extract_archive(archive_path=str(test_zip_file_path), extract_path=str(extracted_images_dir))
        if extraction_success:
            # print(f"압축 해제 성공: {extracted_images_dir}") # 주석 처리
            pass # 성공 시 아무것도 출력 안 함
        else:
            # print(f"압축 해제 실패. 이후 처리를 중단합니다.") # 주석 처리
            exit()
    else:
        # print(f"오류: ZIP 파일({test_zip_file_path})을 찾을 수 없습니다. 처리를 중단합니다.") # 주석 처리
        exit()

    # --- 2. XLSX 파싱 (학번 리스트 추출) ---
    # print(f"\n--- 2. XLSX 파싱 시작 ---") # 주석 처리
    if os.path.exists(test_xlsx_file_path):
        student_id_list_from_xlsx = parsing_xlsx(xlsx_file_path=test_xlsx_file_path)
        if student_id_list_from_xlsx:
            # print(f"학번 리스트 추출 성공 (총 {len(student_id_list_from_xlsx)}개)") # 주석 처리
            pass
        else:
            # print(f"경고: XLSX 파일에서 학번 정보를 추출하지 못했습니다. 빈 리스트로 진행합니다.") # 주석 처리
            student_id_list_from_xlsx = [] 
    else:
        # print(f"오류: XLSX 파일({test_xlsx_file_path})을 찾을 수 없습니다. 학번 리스트 없이 진행합니다.") # 주석 처리
        student_id_list_from_xlsx = []

    # --- 3. 메인 로직 실행 ---
    # print(f"\n--- 3. 학번 인식 메인 로직 실행 ---") # 주석 처리
    result_data = main(answer_sheet_dir_path=extracted_images_dir, student_id_list=student_id_list_from_xlsx)
    
    print("\n--- 처리 결과 ---")
    if result_data:
        print(json.dumps(result_data, ensure_ascii=False, indent=4))
    else:
        print("처리 중 오류가 발생했거나 결과 데이터가 없습니다.")            
    # print("\n--- 테스트 종료 ---") # 주석 처리
