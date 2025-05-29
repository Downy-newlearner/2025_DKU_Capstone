import os
import json
import cv2
from transformers import pipeline
from PIL import Image

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

# 모델 로드
pipe = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)

# 문제 번호 이미지 디렉토리와 답지 정보 JSON 파일을 기반으로 y좌표 정보를 추출하여 JSON 파일로 저장하는 함수
def create_question_info_json(qn_directory_path, answer_json_path):
    # 답지 정보 로드
    with open(answer_json_path, 'r', encoding='utf-8') as f:
        answer_data = json.load(f)

    # 답지 정보 분석하기
    question_list = []
    for question in answer_data['questions']:
        question_number = question['question_number']
        sub_question_number = question.get('sub_question_number', 0)
        if sub_question_number != 0:
            question_list.append(f"{question_number}-{sub_question_number}")
        else:
            question_list.append(str(question_number))

    # question_list에는 모든 문제 번호가 저장됨
    print("Extracted question list:", question_list)

    # 인식된 문제 번호와 y좌표 정보를 저장할 딕셔너리 
    y_coordinates_dict = {}

    # qn_directory_path의 모든 이미지 파일 순회
    for folder in os.listdir(qn_directory_path):
        folder_path = os.path.join(qn_directory_path, folder)
        if os.path.isdir(folder_path):
            for filename in sorted(os.listdir(folder_path)):
                if filename.endswith(('.jpeg', '.jpg', '.png')):
                    file_path = os.path.join(folder_path, filename)
                    # 파일명에서 y_top과 y_bottom 추출
                    parts = filename.split('_')
                    if len(parts) >= 4:
                        y_top = int(parts[2])
                        y_bottom = int(parts[3].split('.')[0])

                        # 이미지 읽기 및 처리
                        image = cv2.imread(file_path)
                        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                        _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                        for contour in contours:
                            x, y, w, h = cv2.boundingRect(contour)
                            cropped_image = image[y:y+h, x:x+w]
                            cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)).convert('RGB')
                            predictions = pipe(cropped_pil_image)
                            if predictions:
                                top_prediction = predictions[0]
                                text, confidence = top_prediction['label'], top_prediction['score']
                                # 인식 결과가 0.85 이상이고 숫자인 경우
                                if confidence > 0.85 and text.isdigit():
                                    y_coordinates_dict[text] = [y_top, y_bottom]
                                # 인식 결과가 0.85 미만인 경우 -> 답지를 통해 예측하는 로직 활용
                                else:
                                    y_coordinates_dict[text] = [y_top, y_bottom]

    # JSON 파일로 저장
    question_info_path = 'question_info.json'
    with open(question_info_path, 'w', encoding='utf-8') as f:
        json.dump(y_coordinates_dict, f, ensure_ascii=False, indent=4)

    print(f"JSON 파일이 생성되었습니다: {question_info_path}")

# 사용 예시
# 문제 번호 이미지 디렉토리 경로와 답지 정보 JSON 파일 경로 설정
qn_directory_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/question_number'
answer_json_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/answer_key.json'
# 함수 호출
create_question_info_json(qn_directory_path, answer_json_path) 