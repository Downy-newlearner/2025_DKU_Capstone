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

client = MongoClient('mongodb://localhost:27017')  # 연결 정보에 맞게 수정
db = client['capstone']
collection = db['exams']


def make_json(processed_dir_path):
    # 디렉토리명(과목명) 추출
    subject = os.path.basename(os.path.normpath(processed_dir_path))
    # JSON 구조 생성
    data = {
        "subject": subject,
        "student_list": [],  # 학번 리스트 추가
        "base64_data": []
    }
    return data

# 메인 처리 함수
def main(answer_sheet_dir_path: str, student_id_list: list): # student_id_list는 인식 성공/실패 판별에 사용
    actual_answer_sheet_dir = answer_sheet_dir_path
    data = make_json(actual_answer_sheet_dir)

    for root, dirs, files in os.walk(actual_answer_sheet_dir):
        for file in files:
            if not file.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            answer_sheet = os.path.join(root, file)
            student_num, cropped_stduend_ID_image_base64_data = extract_student_num(answer_sheet) 
            print(f"DEBUG: Processing {file}, extracted student_num: {student_num}") # student_num 값 확인
            
            # base64 데이터 디버깅
            print(f"DEBUG: Base64 data is None: {cropped_stduend_ID_image_base64_data is None}")
            if cropped_stduend_ID_image_base64_data:
                print(f"DEBUG: Base64 data length: {len(cropped_stduend_ID_image_base64_data)}")
                print(f"DEBUG: Base64 data preview: {cropped_stduend_ID_image_base64_data[:50]}...")
            
            go_to_json = student_num_comparision(student_num, student_id_list)
            print(f"DEBUG: For {file}, student_num_comparision returned: {go_to_json}") # go_to_json 값 확인
            
            # 3. 조건에 따라 결과 저장
            if go_to_json:
                data['student_list'].append(str(student_num))
                data['base64_data'].append(cropped_stduend_ID_image_base64_data)
                print(f"DEBUG: Added base64 data to list. Current list length: {len(data['base64_data'])}")
                continue
            
            else: # go_to_json == False (인식 성공 및 학번부와 8자리 일치)
                if student_num: # student_num이 정상적으로 추출된 경우에만 파일명 변경 시도
                    base, ext = os.path.splitext(file)
                    # student_num_comparision에서 이미 8자리 검증을 했으므로, 여기서 추가 검증은 불필요할 수 있음
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
                    # 이 경우는 student_num_comparision 로직 상 발생하기 어려움
                    # (student_num이 None이면 go_to_json이 True가 되어야 함)
                    print(f"학번 추출 실패(None)했으나 파일명 변경 로직 진입 (예상치 못한 상황): {answer_sheet}")
    
    return data

# 예시 실행 코드
if __name__ == '__main__':
    # --- 설정 ---
    base_dir = "/Users/ohyooseok/캡스톤/capstone_AI/AI/test_data"
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
