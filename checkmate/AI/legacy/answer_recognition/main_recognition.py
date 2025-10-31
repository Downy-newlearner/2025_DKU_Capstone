import json
import os
from recognition.recognition_of_question_number import create_question_info_dict
from recognition.rename_answer_files import rename_answer_files
from recognition.split_and_recognize_single_digits import split_and_recognize_single_digits

# 경로 설정 (이 부분은 Spring으로부터 정보를 받아 동적으로 설정될 수 있도록 변경될 수 있습니다.)
DEFAULT_QN_DIRECTORY_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/question_number'
DEFAULT_ANSWER_JSON_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/answer_key.json'
DEFAULT_ANSWER_DIR_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/answer'
DEFAULT_OCR_RESULTS_JSON_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/JSON/recognition_failures.json'

def make_recognition_json_structure(subject_name: str):
    """
    답안 인식 결과를 담을 기본 JSON 구조를 생성합니다.
    Student_id_recognition/main.py의 make_json과 유사한 역할을 합니다.
    """
    return {
        "subject": subject_name,
        "processed_image_sets": [], # 성공적으로 처리된 이미지 세트(sub_dir)의 답안 정보
        "failed_image_sets": [],  # 처리 실패 또는 건너뛴 이미지 세트(sub_dir) 정보
        "error": None, # 함수 전체의 치명적 오류 메시지
        "warning": None # 함수 전체의 경고 메시지
    }

def main_recognition_process(
    subject_name: str,
    qn_directory_path: str = DEFAULT_QN_DIRECTORY_PATH,
    answer_json_path: str = DEFAULT_ANSWER_JSON_PATH,
    answer_dir_path: str = DEFAULT_ANSWER_DIR_PATH,
    ocr_results_json_path: str = DEFAULT_OCR_RESULTS_JSON_PATH,
    previous_step_json_data: dict = None
):
    """
    2차 답안 인식 전체 플로우를 담당하는 메인 함수입니다.
    """
    recognition_results = make_recognition_json_structure(subject_name)
    
    # ocr_results/JSON 폴더가 없으면 생성
    os.makedirs(os.path.dirname(ocr_results_json_path), exist_ok=True)

    # 1. 문제 번호 정보 딕셔너리 생성
    # create_question_info_dict 함수는 문제 번호 영역 이미지로부터 y좌표를 읽어옵니다.
    # 이 정보는 답안 영역과 문제 번호를 매칭시키는 데 사용됩니다.
    question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)

    if question_info_dict is None:
        error_msg = "Failed to create question_info_dict."
        print(error_msg)
        recognition_results["error"] = error_msg
        return recognition_results

    # 2. 답안 파일 이름 변경 (1차 인식 결과 반영)
    # Spring으로부터 받은 JSON (previous_step_json_data)에 학생 정보 및 파일명 변경 정보가 있다면,
    # rename_answer_files 전에 해당 정보를 사용하여 파일명을 먼저 변경하는 로직이 필요할 수 있습니다.
    # 현재 rename_answer_files는 y좌표와 answer_key.json을 기반으로 파일명을 변경합니다.
    # TODO: 1차 인식 결과를 반영하여 파일명을 변경하는 로직 추가 (필요시)
    try:
        rename_answer_files(question_info_dict, answer_json_path, answer_dir_path)
        print(f"답안 파일 이름 변경 완료 (경로: {answer_dir_path})")
    except Exception as e:
        error_msg = f"Error during renaming answer files: {e}"
        print(error_msg)
        recognition_results["error"] = error_msg
        return recognition_results

    # 3. 이미지 전처리 및 답안 인식
    # text_crop 이미지들이 이미 answer_dir_path에 준비되어 있다고 가정합니다.
    # split_and_recognize_single_digits 함수는 이 경로를 입력으로 받습니다.
    print(f"답안 인식 시작 (입력 경로: {answer_dir_path})")
    # split_and_recognize_single_digits는 answer_dir_path내의 sub_dir들을 처리
    digit_recognition_outputs = split_and_recognize_single_digits(
        directory_path=answer_dir_path, 
        failed_recognition_json_path=ocr_results_json_path
    )

    if not digit_recognition_outputs:
        warning_msg = f"split_and_recognize_single_digits returned no output. Check logs. Input path: {answer_dir_path}"
        print(warning_msg)
        recognition_results["warning"] = warning_msg
        # 출력이 없더라도, ocr_results_json_path 파일에 실패 로그가 있을 수 있음
        # 여기서 반환할지, 아니면 빈 결과라도 아래 로직을 태울지 결정
        # 여기서는 일단 반환하지 않고 아래 로직으로 진행하여 failed_image_sets에라도 기록되도록 함.

    # 4. 인식 결과 통합
    processed_sets_count = 0
    for image_set_name, result_data in digit_recognition_outputs.items():
        if result_data.get('status') == 'success':
            recognition_results["processed_image_sets"].append({
                "original_image_set": image_set_name,
                "recognized_answers": result_data.get("recognized_answers", [])
            })
            processed_sets_count += 1
        else:
            recognition_results["failed_image_sets"].append({
                "original_image_set": image_set_name,
                "status": result_data.get('status', 'unknown_failure'),
                "reason": result_data.get('reason', 'No specific reason provided.'),
                "failed_crops": result_data.get('failed_crops', [])
            })

    if not digit_recognition_outputs and not os.path.exists(ocr_results_json_path):
         # 이 경우는 split_and_recognize_single_digits가 빈 결과를 반환했고, 실패 로그 파일도 생성하지 않은 경우
        recognition_results["warning"] = (recognition_results.get("warning", "") + 
                                          " Also, no failure log JSON was created.").strip()

    if processed_sets_count == 0 and not recognition_results["failed_image_sets"]:
        if not recognition_results.get("warning"): # 중복 경고 방지
            final_warning = f"No image sets were processed successfully or marked as failed from {answer_dir_path}."
            print(final_warning)
            recognition_results["warning"] = (recognition_results.get("warning", "") + f" {final_warning}").strip()
    
    print(f"답안 인식 완료. 성공 세트: {processed_sets_count}, 실패/건너뛴 세트: {len(recognition_results['failed_image_sets'])}")
    return recognition_results

if __name__ == '__main__':
    # 이 부분은 Flask 앱에서 라우트 핸들러가 호출하는 방식으로 변경될 것입니다.
    # 테스트를 위한 예시 실행
    subject = "SampleSubject_OCR_Test"

    # 1차 학번 인식 단계에서 생성되었을 법한 JSON (예시)
    # 실제로는 Spring을 통해 이 데이터가 전달됩니다.
    mock_student_id_results = {
        "subject": subject,
        "student_list": [], 
        "base64_data": [] 
    }

    print(f"--- 테스트 시작: {subject} ---")
    print(f"사용될 QN 디렉토리: {DEFAULT_QN_DIRECTORY_PATH}")
    print(f"사용될 Answer JSON: {DEFAULT_ANSWER_JSON_PATH}")
    print(f"사용될 Answer 디렉토리 (OCR 대상): {DEFAULT_ANSWER_DIR_PATH}")
    print(f"OCR 실패 로그 JSON 경로: {DEFAULT_OCR_RESULTS_JSON_PATH}")

    final_output = main_recognition_process(
        subject_name=subject,
        # qn_directory_path=DEFAULT_QN_DIRECTORY_PATH, # 기본값 사용
        # answer_json_path=DEFAULT_ANSWER_JSON_PATH,   # 기본값 사용
        # answer_dir_path=DEFAULT_ANSWER_DIR_PATH,     # 기본값 사용
        # ocr_results_json_path=DEFAULT_OCR_RESULTS_JSON_PATH, # 기본값 사용
        previous_step_json_data=mock_student_id_results
    )

    print("\n--- 최종 답안 인식 통합 결과 JSON ---")
    print(json.dumps(final_output, ensure_ascii=False, indent=2))

    # 실패 로그 파일 내용 확인 (테스트용)
    if os.path.exists(DEFAULT_OCR_RESULTS_JSON_PATH):
        try:
            with open(DEFAULT_OCR_RESULTS_JSON_PATH, 'r') as f_log:
                print("\n--- OCR 실패 로그 파일 내용 ---")
                print(f_log.read())
        except Exception as e:
            print(f"\nOCR 실패 로그 파일 읽기 오류: {e}")

# 기존 코드 주석 처리 또는 필요시 통합
# # 문제 번호 정보 딕셔너리 생성
# question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)
#
# # 답안 파일 이름 변경
# if question_info_dict is not None:
#     rename_answer_files(question_info_dict, answer_json_path, answer_dir_path)
# else:
#     print("문제 번호 정보 딕셔너리를 생성하는 데 실패했습니다.")
