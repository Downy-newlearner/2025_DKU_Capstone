import json
from .student_num_comparision.student_num_comparision import student_num_comparision
from .extract_student_num.extract_student_num import extract_student_num
# from .decompression_parsing.parsing_xlsx import parsing_xlsx # main 함수에서 직접 사용 안함
# from .decompression_parsing.decompression import extract_archive # main 함수에서 직접 사용 안함
import os
# import shutil # main 함수에서 직접 사용 안함
# from pathlib import Path # main 함수에서 직접 사용 안함
# from pymongo import MongoClient # main 함수에서 직접 사용 안함
# from bson import ObjectId # main 함수에서 직접 사용 안함
import base64
import unicodedata # 유니코드 정규화를 위해 추가

# client = MongoClient('mongodb://localhost:27017') # main 함수에서 직접 사용 안함
# db = client['capstone'] # main 함수에서 직접 사용 안함
# collection = db['exams'] # main 함수에서 직접 사용 안함


def make_json(processed_dir_path):
    # 디렉토리명(과목명) 추출
    # subject = os.path.basename(os.path.normpath(processed_dir_path)) # 이제 main 함수에서 subject_name을 받음
    # JSON 구조 생성
    data = {
        # "subject": subject, # subject는 main 함수에서 최종적으로 설정
        "images": []
    }

    allowed_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')

    try:
        for filename_raw in os.listdir(processed_dir_path):
            filename_nfc = unicodedata.normalize('NFC', filename_raw)
            if filename_nfc.lower().endswith(allowed_extensions):
                file_path_raw = os.path.join(processed_dir_path, filename_raw) # 원본 파일명으로 경로 구성
                if os.path.isfile(file_path_raw):
                    try:
                        with open(file_path_raw, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                        
                        data["images"].append({
                            "file_name": filename_nfc, # JSON에는 NFC 정규화된 파일명 저장
                            "base64_data": encoded_string
                        })
                    except Exception as e:
                        print(f"Error processing file {file_path_raw}: {e}")
    except FileNotFoundError:
        print(f"Error: Directory not found at {processed_dir_path}")
    except PermissionError:
        print(f"Error: Permission denied for directory {processed_dir_path}")
    except Exception as e:
        print(f"An unexpected error occurred while accessing directory {processed_dir_path}: {e}")

    return data

# 메인 처리 함수
def main(answer_sheet_dir_path: str, student_id_list: list, subject_name: str) -> dict: # subject_name 인자 추가
    actual_answer_sheet_dir = unicodedata.normalize('NFC', answer_sheet_dir_path) # 경로도 NFC 정규화
    
    # make_json은 디렉토리 내 모든 이미지의 base64를 미리 로드함.
    # 파일명 변경 후에는 이 정보가 부정확해질 수 있으므로, 
    # result_json['images']는 실패한 경우에만 채우는 방식으로 변경됨.
    # 따라서 make_json 호출은 여기서 제거하고, 실패 시 필요한 데이터만 수집.
    result_json = {
        "subject": unicodedata.normalize('NFC', subject_name), # Kafka로 보낼 subject 명확화
        "images": [] # 인식 실패 또는 오류 발생 시 추가될 이미지 정보
    }

    # os.walk는 raw 파일명을 반환할 수 있으므로, 모든 경로와 파일명에 NFC 정규화 적용
    for root_raw, dirs_raw, files_raw in os.walk(actual_answer_sheet_dir):
        root_nfc = unicodedata.normalize('NFC', root_raw)
        
        # __MACOSX 폴더 자체를 탐색에서 제외 (dirs_raw는 변경하지 않고, root_nfc 경로 체크로 필터링)
        if '__MACOSX' in root_nfc.split(os.sep): # 경로 분리 후 __MACOSX 포함 여부 확인
            continue
            
        dirs_to_remove = [d for d in dirs_raw if unicodedata.normalize('NFC', d) == '__MACOSX']
        for d_remove in dirs_to_remove:
            dirs_raw.remove(d_remove) # os.walk가 하위 디렉토리로 들어가지 않도록 dirs_raw에서 제거

        for file_raw in files_raw:
            original_filename_nfc = unicodedata.normalize('NFC', file_raw)

            if original_filename_nfc.startswith('._') or not original_filename_nfc.lower().endswith(('.png', '.jpg', '.jpeg')) :
                continue
                
            answer_sheet_path_raw = os.path.join(root_raw, file_raw) # rename 시 사용할 원본(raw) 전체 경로
            # answer_sheet_path_nfc = os.path.join(root_nfc, original_filename_nfc) # 이 줄은 주석 처리하거나 사용하지 않음

            # YOLO에는 원본(raw) 경로를 전달
            student_num_raw, cropped_student_ID_image_base64_data = extract_student_num(answer_sheet_path_raw) 
            
            student_num_nfc = None
            if student_num_raw is not None: # student_num_raw가 None이 아닐 때만 처리
                # OCR 결과가 정수형일 수 있으므로 문자열로 변환 후 정규화
                student_num_nfc = unicodedata.normalize('NFC', str(student_num_raw))

            print(f"DEBUG: Processing {original_filename_nfc}, extracted student_num_nfc: {student_num_nfc}")
            
            # Base64 데이터 로깅 부분 (생략 가능)
            # if cropped_student_ID_image_base64_data:
            #     print(f"DEBUG: Base64 data length for {original_filename_nfc}: {len(cropped_student_ID_image_base64_data)}")

            # 학적부의 student_id_list도 NFC 정규화된 상태라고 가정 (또는 여기서 정규화)
            student_id_list_nfc = [unicodedata.normalize('NFC', sid) for sid in student_id_list]
            
            go_to_json = student_num_comparision(student_num_nfc, student_id_list_nfc) # 비교도 NFC 정규화된 학번으로
            print(f"DEBUG: For {original_filename_nfc}, student_num_comparision returned: {go_to_json}")
            
            if go_to_json: # 학번이 없거나(None), 학적부에 없어서 2차 수정 대상으로 넘어가는 경우
                result_json['images'].append({
                    "file_name": original_filename_nfc,
                    "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else ""
                })
                print(f"DEBUG: Added base64 data to result_json for {original_filename_nfc}.")
                continue # 파일명 변경 없이 다음 파일로
            
            else: # 학번이 있고(not None), 학적부에도 있는 경우 (go_to_json == False)
                if student_num_nfc: # 이 시점에서 student_num_nfc는 유효한 학번이어야 함
                    base_raw, ext_raw = os.path.splitext(file_raw) # 원본(raw) 파일명에서 확장자 추출
                    
                    # 새 파일명: subject_학번.확장자 (모두 NFC 정규화)
                    # subject_name은 이미 NFC 정규화됨, student_num_nfc도 NFC 정규화됨
                    new_filename_nfc = f"{result_json['subject']}_{student_num_nfc}{ext_raw if ext_raw else '.jpg'}"
                    new_file_path_nfc = os.path.join(root_nfc, new_filename_nfc) # 새 파일 경로도 NFC 기준
                    
                    # 자기 자신으로의 변경인지 확인 (원본 raw 파일명을 NFC로 바꿔서 새 NFC 파일명과 비교)
                    if unicodedata.normalize('NFC', file_raw) == new_filename_nfc:
                        print(f"INFO: File {original_filename_nfc} already has the target name {new_filename_nfc}. No change.")
                        continue

                    # 새 파일 경로가 이미 존재하는지 확인 (NFC 경로 기준)
                    # 하지만 rename은 raw 경로를 사용해야 할 수 있으므로, 실제 rename 대상은 answer_sheet_path_raw
                    # 새 파일명은 new_filename_nfc를 raw 경로인 root_raw와 합쳐서 사용해야 함
                    # new_file_path_for_os_rename = os.path.join(root_raw, new_filename_nfc) -> 잠재적 문제: new_filename_nfc는 NFC인데 root_raw는 raw
                    # 따라서, new_filename_nfc를 os.rename 하기 전에, 파일 시스템이 이해할 형태로 변환하거나,
                    # 혹은 os.rename(raw_old, raw_new) 형태로 가야함.
                    # 여기서는 new_filename_nfc는 그대로 두고, os.rename(raw_old_path, nfc_new_path) 시도
                    
                    new_file_path_target_for_os = os.path.join(root_raw, new_filename_nfc)


                    if os.path.exists(new_file_path_target_for_os):
                        print(f"WARNING: Target file path {new_file_path_target_for_os} already exists. Skipping rename for {file_raw}.")
                    else:
                        try:
                            os.rename(answer_sheet_path_raw, new_file_path_target_for_os)
                            print(f"SUCCESS: Renamed RAW: {answer_sheet_path_raw} -> NEW_NFC_NAME_IN_RAW_DIR: {new_file_path_target_for_os}")
                        except Exception as e:
                            print(f"ERROR: Failed to rename RAW: {answer_sheet_path_raw} to NEW_NFC_NAME_IN_RAW_DIR: {new_file_path_target_for_os}. Error: {e}")
                            result_json['images'].append({
                                "file_name": original_filename_nfc,
                                "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else "",
                                "rename_error": str(e)
                            })       
                else: 
                    # 이 경우는 student_num_comparision 로직상 발생하기 어려움 (student_num이 None이면 go_to_json=True가 되어야 함)
                    print(f"WARNING: Student ID is None but comparison logic passed for {original_filename_nfc}. This is unexpected.")
                    result_json['images'].append({
                        "file_name": original_filename_nfc,
                        "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else "",
                        "error_description": "Student ID is None but comparison logic passed (unexpected)."
                    })
    
    return result_json

# 예시 실행 코드
if __name__ == '__main__':
    # --- 설정 ---
    base_dir = "/home/jdh251425/2025_DKU_Capstone/AI/test_data"
    test_zip_file_path = os.path.join(base_dir, "test_answer.zip")
    test_xlsx_file_path = os.path.join(base_dir, "학적정보.xlsx")
    
    extracted_images_dir_raw = os.path.join(base_dir, os.path.splitext(os.path.basename(test_zip_file_path))[0])

    test_subject_name = "컴퓨터비전" 

    # if __name__ 블록에서만 사용되는 import
    import shutil 
    from pathlib import Path 
    from .decompression_parsing.parsing_xlsx import parsing_xlsx 
    from .decompression_parsing.decompression import extract_archive 
    # json.dumps를 사용하므로 json import 추가 (main.py 상단에 이미 있다면 중복이지만, 안전하게 추가)
    import json 

    print("--- 테스트 준비 ---")
    print(f"입력 ZIP 파일: {test_zip_file_path}")
    print(f"학적 정보 XLSX 파일: {test_xlsx_file_path}")
    print(f"압축 해제 목표 디렉토리 (raw name): {extracted_images_dir_raw}")
    print(f"테스트 과목명: {test_subject_name}")

    # --- 1. 압축 해제 ---
    if os.path.exists(test_zip_file_path):
        if os.path.exists(extracted_images_dir_raw):
            print(f"기존 압축 해제 폴더 {extracted_images_dir_raw} 삭제 중...")
            shutil.rmtree(extracted_images_dir_raw)
        extraction_success = extract_archive(archive_path=str(test_zip_file_path), extract_path=str(extracted_images_dir_raw))
        if not extraction_success:
            print("압축 해제 실패. 이후 처리를 중단합니다.")
            exit()
        else:
            print(f"압축 해제 성공: {extracted_images_dir_raw}")
    else:
        print(f"오류: ZIP 파일({test_zip_file_path})을 찾을 수 없습니다. 처리를 중단합니다.")
        exit()

    # --- 2. XLSX 파싱 (학번 리스트 추출) ---
    print("\n--- 2. XLSX 파싱 시작 ---")
    if os.path.exists(test_xlsx_file_path):
        student_id_list_from_xlsx = parsing_xlsx(xlsx_file_path=test_xlsx_file_path)
        if student_id_list_from_xlsx:
            print(f"학번 리스트 추출 성공 (총 {len(student_id_list_from_xlsx)}개): {student_id_list_from_xlsx[:5]}...")
        else:
            print("경고: XLSX 파일에서 학번 정보를 추출하지 못했습니다. 빈 리스트로 진행합니다.")
            student_id_list_from_xlsx = [] 
    else:
        print(f"오류: XLSX 파일({test_xlsx_file_path})을 찾을 수 없습니다. 학번 리스트 없이 진행합니다.")
        student_id_list_from_xlsx = []

    # --- 3. 메인 로직 실행 ---
    print(f"\n--- 3. 학번 인식 메인 로직 실행 ({test_subject_name} 과목) ---")
    
    result_data = main(answer_sheet_dir_path=extracted_images_dir_raw, 
                       student_id_list=student_id_list_from_xlsx, 
                       subject_name=test_subject_name)
    
    print("\n--- 처리 결과 JSON ---")
    if result_data:
        print(json.dumps(result_data, ensure_ascii=False, indent=4))
    else:
        print("처리 중 오류가 발생했거나 결과 데이터가 없습니다.")            
    print("\n--- 테스트 종료 ---")
