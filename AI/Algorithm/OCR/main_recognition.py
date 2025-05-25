import json
import os
from recognition.recognition_of_question_number import create_question_info_dict
from recognition.rename_answer_files import rename_answer_files

# 경로 설정 (이 부분은 Spring으로부터 정보를 받아 동적으로 설정될 수 있도록 변경될 수 있습니다.)
DEFAULT_QN_DIRECTORY_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/question_number'
DEFAULT_ANSWER_JSON_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/answer_key.json'
DEFAULT_ANSWER_DIR_PATH = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/answer'

def make_recognition_json_structure(subject_name: str):
    """
    답안 인식 결과를 담을 기본 JSON 구조를 생성합니다.
    Student_id_recognition/main.py의 make_json과 유사한 역할을 합니다.
    """
    return {
        "subject": subject_name,
        "recognized_answers": [], # 인식된 답안 정보를 저장할 리스트
        "failed_recognition": []  # 인식 실패 정보를 저장할 리스트 (이미지 base64, 파일명 등)
    }

def main_recognition_process(
    subject_name: str,
    qn_directory_path: str = DEFAULT_QN_DIRECTORY_PATH,
    answer_json_path: str = DEFAULT_ANSWER_JSON_PATH,
    answer_dir_path: str = DEFAULT_ANSWER_DIR_PATH,
    # Spring으로부터 받은 JSON 데이터를 처리하기 위한 파라미터 추가 가능
    # 예를 들어, student_id_recognition 결과 JSON 등
    previous_step_json_data: dict = None
):
    """
    2차 답안 인식 전체 플로우를 담당하는 메인 함수입니다.
    """
    recognition_results = make_recognition_json_structure(subject_name)

    # 1. 문제 번호 정보 딕셔너리 생성
    # create_question_info_dict 함수는 문제 번호 영역 이미지로부터 y좌표를 읽어옵니다.
    # 이 정보는 답안 영역과 문제 번호를 매칭시키는 데 사용됩니다.
    question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)

    if question_info_dict is None:
        print("문제 번호 정보 딕셔너리를 생성하는 데 실패했습니다.")
        # 실패 시 Spring에 전달할 JSON에 에러 정보 추가 가능
        recognition_results["error"] = "Failed to create question_info_dict"
        return recognition_results # 또는 에러 처리

    # 2. 답안 파일 이름 변경 (1차 인식 결과 반영)
    # Spring으로부터 받은 JSON (previous_step_json_data)에 학생 정보 및 파일명 변경 정보가 있다면,
    # rename_answer_files 전에 해당 정보를 사용하여 파일명을 먼저 변경하는 로직이 필요할 수 있습니다.
    # 현재 rename_answer_files는 y좌표와 answer_key.json을 기반으로 파일명을 변경합니다.
    # TODO: 1차 인식 결과를 반영하여 파일명을 변경하는 로직 추가 (필요시)

    # rename_answer_files 함수는 question_info_dict와 answer_key.json을 참고하여
    # answer_dir_path 내의 답안 이미지 파일명을 (기존파일명)_qn_{문제번호}_ac_{정답개수}.{확장자} 형식으로 변경합니다.
    rename_answer_files(question_info_dict, answer_json_path, answer_dir_path)
    print(f"답안 파일 이름 변경 완료 (경로: {answer_dir_path})")

    # 3. 이미지 전처리 및 답안 인식 (상세 로직 추가 필요)
    #   - Algorithm/OCR/preprocessing/text_crop.py 등을 사용하여 이미지 전처리
    #   - Algorithm/OCR/recognition/split_and_recognize_single_digits.py 등을 사용하여 답안 인식
    #   - 인식 결과를 recognition_results["recognized_answers"]에 추가
    #   - 인식 실패 시 recognition_results["failed_recognition"]에 정보 추가

    # 예시: answer_dir_path에서 파일 목록을 가져와서 처리한다고 가정
    processed_files_count = 0
    for root, _, files in os.walk(answer_dir_path):
        for file in files:
            if file.startswith('.'): # .DS_Store와 같은 숨김 파일 제외
                continue
            # TODO: 실제 전처리 및 인식 로직 호출
            # 예: recognized_data, failed_data = process_single_image(os.path.join(root, file))
            # if recognized_data:
            #     recognition_results["recognized_answers"].append(recognized_data)
            # if failed_data:
            #     recognition_results["failed_recognition"].append(failed_data)
            processed_files_count += 1
            # 임시로 인식 성공/실패를 구분하지 않고 파일명만 추가
            recognition_results["recognized_answers"].append({"filename": file, "status": "pending_actual_recognition"})


    if processed_files_count == 0:
        print(f"처리할 답안 이미지가 없습니다. (경로: {answer_dir_path})")
        recognition_results["warning"] = f"No answer images found in {answer_dir_path}"


    # 4. 인식 실패 JSON 생성 (이미 위에서 failed_recognition 리스트에 추가)
    # Spring에 전달할 최종 JSON 반환
    return recognition_results









if __name__ == '__main__':
    # 이 부분은 Flask 앱에서 라우트 핸들러가 호출하는 방식으로 변경될 것입니다.
    # 테스트를 위한 예시 실행
    subject = "SampleSubject" # 예시 과목명

    # 1차 학번 인식 단계에서 생성되었을 법한 JSON (예시)
    # 실제로는 Spring을 통해 이 데이터가 전달됩니다.
    mock_student_id_results = {
        "subject": subject,
        "student_list": ["(SampleSubject)_(32000000).jpg", "(SampleSubject)_(32000001).jpg"], # 성공적으로 학번이 매칭된 파일명 리스트
        "base64_data": [] # 학번 매칭 실패 이미지 정보 (파일명, base64)
    }

    # main_recognition_process 함수 호출
    # 실제 환경에서는 Flask 엔드포인트가 이 함수를 호출하고,
    # 필요한 경로 정보나 이전 단계의 JSON 데이터를 인자로 전달합니다.
    final_recognition_output = main_recognition_process(
        subject_name=subject,
        # qn_directory_path, answer_json_path, answer_dir_path는 필요에 따라 인자로 전달 가능
        previous_step_json_data=mock_student_id_results
    )

    print("\\n--- 최종 답안 인식 결과 JSON ---")
    print(json.dumps(final_recognition_output, ensure_ascii=False, indent=2))

# 기존 코드 주석 처리 또는 필요시 통합
# # 문제 번호 정보 딕셔너리 생성
# question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)
#
# # 답안 파일 이름 변경
# if question_info_dict is not None:
#     rename_answer_files(question_info_dict, answer_json_path, answer_dir_path)
# else:
#     print("문제 번호 정보 딕셔너리를 생성하는 데 실패했습니다.")
