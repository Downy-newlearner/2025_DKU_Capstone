'''
주석 작성: 정다훈 250525

create_question_info_dict 함수:

Params:
    - qn_directory_path
    - answer_json_path

Return:
    - y_coordinates_dict

'''


import os
import json

# 문제 번호 이미지 디렉토리와 답지 정보 JSON 파일을 기반으로 y좌표 정보를 추출하여 딕셔너리를 반환하는 함수
def create_question_info_dict(qn_directory_path, answer_json_path):
    # 답지 정보 로드
    with open(answer_json_path, 'r', encoding='utf-8') as f:
        answer_data = json.load(f)

    # 리스트 a와 b 생성
    question_list_a = []
    question_list_b = set()
    for question in answer_data['questions']:
        question_number = question['question_number']
        sub_question_number = question.get('sub_question_number', 0)
        if sub_question_number != 0:
            question_list_a.append(f"{question_number}-{sub_question_number}")
        else:
            question_list_a.append(str(question_number))
        question_list_b.add(str(question_number))

    # 디렉토리에서 y_top, y_bottom 추출
    y_coordinates_list = []
    for folder in os.listdir(qn_directory_path):
        parts = folder.split('_')
        if len(parts) >= 4:
            y_top = int(parts[2])
            y_bottom = int(parts[3].split('.')[0])
            y_coordinates_list.append((y_top, y_bottom))

    # y_top 기준으로 정렬
    y_coordinates_list.sort()

    # 경우의 수에 따라 처리
    y_coordinates_dict = {}
    if len(question_list_a) == len(y_coordinates_list):
        # 경우의 수 1
        for i, (y_top, y_bottom) in enumerate(y_coordinates_list):
            y_coordinates_dict[question_list_a[i]] = [y_top, y_bottom]
    elif len(question_list_b) == len(y_coordinates_list):
        # 경우의 수 2
        question_list_b = sorted(question_list_b)
        for i, (y_top, y_bottom) in enumerate(y_coordinates_list):
            y_coordinates_dict[question_list_b[i]] = [y_top, y_bottom]
    else:
        # 경우의 수 3
        print("type A, B 모두 일치하지 않습니다")
        return None

    return y_coordinates_dict

# 사용 예시
qn_directory_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/question_number'
answer_json_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/answer_key.json'
question_info_dict = create_question_info_dict(qn_directory_path, answer_json_path)
print(question_info_dict) 