from recognition.recognition_of_question_number import create_question_info_dict
from recognition.rename_answer_files import rename_answer_files

# 경로 설정
qn_directory_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/question_number'
answer_json_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/answer_key.json'
answer_dir_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/answer'

# 문제 번호 정보 딕셔너리 생성
question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)

# 답안 파일 이름 변경
if question_info_dict is not None:
    rename_answer_files(question_info_dict, answer_json_path, answer_dir_path)
else:
    print("문제 번호 정보 딕셔너리를 생성하는 데 실패했습니다.")
