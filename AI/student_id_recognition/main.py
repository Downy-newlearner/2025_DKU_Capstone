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
import traceback # traceback 추가

# client = MongoClient('mongodb://localhost:27017') # main 함수에서 직접 사용 안함
# db = client['capstone'] # main 함수에서 직접 사용 안함
# collection = db['exams'] # main 함수에서 직접 사용 안함


def make_json(processed_dir_path):
    # 디렉토리명(과목명) 추출
    # subject = os.path.basename(os.path.normpath(processed_dir_path)) # 이제 main 함수에서 subject_name을 받음
    # JSON 구조 생성
    data = {
        # "subject": subject, # subject는 main 함수에서 최종적으로 설정
        "lowConfidenceImages": []
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
                        
                        data["lowConfidenceImages"].append({
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
def main(answer_sheet_dir_path: str, 
         student_id_list: list, 
         subject_name: str,
         kafka_producer,
         kafka_topic: str,
         task_id: str
         ) -> dict: # subject_name 인자 추가
    
    normalized_subject_name = unicodedata.normalize('NFC', subject_name) if subject_name else "UNKNOWN_SUBJECT"

    try: 
        if kafka_producer:
            pending_message = {
                "task_id": task_id,
                "subject": normalized_subject_name,
                "status": "PENDING"
            }
            kafka_producer.send(kafka_topic, pending_message)
            print(f"DEBUG: [main.py] Sent PENDING Kafka message for task_id: {task_id}, subject: {normalized_subject_name}")

        actual_answer_sheet_dir = unicodedata.normalize('NFC', answer_sheet_dir_path)
        
        result_data_internal = {
            "subject": normalized_subject_name, 
            "lowConfidenceImages": [] 
        }

        print(f"DEBUG: [main function in main.py] Starting os.walk for directory: {actual_answer_sheet_dir}") 

        for root_raw, dirs_raw, files_raw in os.walk(actual_answer_sheet_dir):
            root_nfc = unicodedata.normalize('NFC', root_raw)
            
            if '__MACOSX' in root_nfc.split(os.sep): 
                continue
            
            dirs_to_remove = [d for d in dirs_raw if unicodedata.normalize('NFC', d) == '__MACOSX']
            for d_remove in dirs_to_remove:
                dirs_raw.remove(d_remove) 

            for file_raw in files_raw:
                original_filename_nfc = unicodedata.normalize('NFC', file_raw)

                if original_filename_nfc.startswith('._') or not original_filename_nfc.lower().endswith(('.png', '.jpg', '.jpeg')) :
                    continue
                
                answer_sheet_path_raw = os.path.join(root_raw, file_raw) 
                
                student_num_raw, cropped_student_ID_image_base64_data = extract_student_num(answer_sheet_path_raw) 
                
                student_num_nfc = None
                if student_num_raw is not None: 
                    student_num_nfc = unicodedata.normalize('NFC', str(student_num_raw))

                print(f"DEBUG: Processing {original_filename_nfc}, extracted student_num_nfc: {student_num_nfc}")
                
                student_id_list_nfc = [unicodedata.normalize('NFC', sid) for sid in student_id_list]
                
                go_to_json = student_num_comparision(student_num_nfc, student_id_list_nfc) 
                print(f"DEBUG: For {original_filename_nfc}, student_num_comparision returned: {go_to_json}")
                
                if go_to_json: 
                    result_data_internal['lowConfidenceImages'].append({
                        "file_name": original_filename_nfc,
                        "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else ""
                    })
                    print(f"DEBUG: Added base64 data to result_data_internal for {original_filename_nfc}.")
                    continue 
                
                else: 
                    if student_num_nfc: 
                        base_raw, ext_raw = os.path.splitext(file_raw) 
                        
                        new_filename_nfc = f"{result_data_internal['subject']}_{student_num_nfc}{ext_raw if ext_raw else '.jpg'}"
                        new_file_path_nfc = os.path.join(root_nfc, new_filename_nfc) 
                        
                        if unicodedata.normalize('NFC', file_raw) == new_filename_nfc:
                            print(f"INFO: File {original_filename_nfc} already has the target name {new_filename_nfc}. No change.")
                            continue
                        
                        new_file_path_target_for_os = os.path.join(root_raw, new_filename_nfc)

                        if os.path.exists(new_file_path_target_for_os):
                            print(f"WARNING: Target file path {new_file_path_target_for_os} already exists. Skipping rename for {file_raw}.")
                        else:
                            try:
                                os.rename(answer_sheet_path_raw, new_file_path_target_for_os)
                                print(f"SUCCESS: Renamed RAW: {answer_sheet_path_raw} -> NEW_NFC_NAME_IN_RAW_DIR: {new_file_path_target_for_os}")
                            except Exception as e:
                                print(f"ERROR: Failed to rename RAW: {answer_sheet_path_raw} to NEW_NFC_NAME_IN_RAW_DIR: {new_file_path_target_for_os}. Error: {e}")
                                result_data_internal['lowConfidenceImages'].append({
                                    "file_name": original_filename_nfc,
                                    "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else "",
                                    "rename_error": str(e)
                                })       
                    else: 
                        print(f"WARNING: Student ID is None but comparison logic passed for {original_filename_nfc}. This is unexpected.")
                        result_data_internal['lowConfidenceImages'].append({
                            "file_name": original_filename_nfc,
                            "base64_data": cropped_student_ID_image_base64_data if cropped_student_ID_image_base64_data else "",
                            "error_description": "Student ID is None but comparison logic passed (unexpected)."
                        })
        
        print(f"DEBUG: [main function in main.py] Finished os.walk. About to send DONE Kafka message.")
        
        if kafka_producer:
            done_payload = {
                "task_id": task_id,
                "status": "DONE",
                "subject": result_data_internal["subject"],
                "lowConfidenceImages": result_data_internal["lowConfidenceImages"]
            }
            print(f"DEBUG: [main.py] Kafka 'DONE' message payload to be sent: {json.dumps(done_payload, ensure_ascii=False, indent=2)}")
            kafka_producer.send(kafka_topic, done_payload)
            kafka_producer.flush()
            print(f"DEBUG: [main.py] Sent DONE Kafka message for task_id: {task_id}")

        return {
            "status": "DONE",
            "message": "Processing completed successfully in student_id_recognition.main.",
            "task_id": task_id,
            "subject": result_data_internal["subject"],
            "lowConfidenceImages": result_data_internal["lowConfidenceImages"]
        }

    except Exception as e:
        print(f"!!!!!!!! ERROR in student_id_recognition.main.main !!!!!!!!")
        print(f"Exception type: {type(e)}")
        print(f"Exception message: {str(e)}")
        print("Traceback:")
        traceback.print_exc() 
        
        if kafka_producer:
            error_payload = {
                "task_id": task_id,
                "subject": normalized_subject_name,
                "status": "ERROR",
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
            print(f"DEBUG: [main.py] Kafka 'ERROR' message payload to be sent: {json.dumps(error_payload, ensure_ascii=False, indent=2)}")
            kafka_producer.send(kafka_topic, error_payload)
            kafka_producer.flush()
            print(f"DEBUG: [main.py] Sent ERROR Kafka message for task_id: {task_id}")

        return {
            "status": "ERROR",
            "message": f"Error during processing in student_id_recognition.main: {str(e)}",
            "task_id": task_id,
            "subject": normalized_subject_name,
            "lowConfidenceImages": [], 
            "error_details": str(e),
            "traceback": traceback.format_exc()
        }

# 예시 실행 코드
if __name__ == '__main__':
    # --- 설정 ---
    base_dir = "/home/jdh251425/2025_DKU_Capstone/AI/test_data"
    test_zip_file_path = os.path.join(base_dir, "test_answer.zip")
    test_xlsx_file_path = os.path.join(base_dir, "학적정보.xlsx")
    
    extracted_images_dir_raw = os.path.join(base_dir, os.path.splitext(os.path.basename(test_zip_file_path))[0])

    test_subject_name = "신호및시스템-1" 
    test_task_id = "test_task_123" # 테스트용 task_id
    test_kafka_topic = "student_id_results_test" # 테스트용 Kafka 토픽

    # if __name__ 블록에서만 사용되는 import
    import shutil 
    from pathlib import Path 
    from .decompression_parsing.parsing_xlsx import parsing_xlsx 
    from .decompression_parsing.decompression import extract_archive 
    # json.dumps를 사용하므로 json import 추가 (main.py 상단에 이미 있다면 중복이지만, 안전하게 추가)
    # import json # 이미 상단에 있음

    # Kafka Producer 모킹 (실제 Kafka 없이 테스트하기 위함)
    class MockKafkaProducer:
        def send(self, topic, value):
            print(f"MOCK KAFKA: Topic='{topic}', Value={json.dumps(value, ensure_ascii=False, indent=2)}")
        def flush(self):
            print("MOCK KAFKA: Flushed.")

    mock_producer = MockKafkaProducer()

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
    
    # main 함수 호출 시 Kafka 관련 인자 전달
    result_data = main(answer_sheet_dir_path=extracted_images_dir_raw, 
                       student_id_list=student_id_list_from_xlsx, 
                       subject_name=test_subject_name,
                       kafka_producer=mock_producer, # Mock 프로듀서 사용
                       kafka_topic=test_kafka_topic,
                       task_id=test_task_id)
    
    print("\n--- main 함수 반환 결과 ---")
    if result_data:
        print(json.dumps(result_data, ensure_ascii=False, indent=4))
    else:
        print("처리 중 오류가 발생했거나 결과 데이터가 없습니다.")            
    print("\n--- 테스트 종료 ---")
