'''

Written by 정다훈 2025.04.13
crop된 모든 이미지에 OCR을 수행하고, 결과를 저장하는 프로그램


recognizing_question_number 함수
파라미터:
  - question_number_path: 질문 번호 이미지가 저장된 디렉토리 경로
리턴값:
  - DataFrame: 인식된 질문 번호와 관련 정보를 담고 있는 데이터프레임

recognizing_answer 함수
파라미터:
  - answer_path: 답변 이미지가 저장된 디렉토리 경로
리턴값:
  - DataFrame: 인식된 답변과 관련 정보를 담고 있는 데이터프레임

'''



import os
import cv2
from easyocr import Reader
import pandas as pd

def recognizing_question_number(question_number_path):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=True,
                    model_storage_directory='model',
                    user_network_directory='user_network',
                    recog_network='custom')

    # 결과를 저장할 리스트
    results = []

    # 각 디렉토리 순회
    for dir_name in os.listdir(question_number_path):
        dir_path = os.path.join(question_number_path, dir_name)
        if os.path.isdir(dir_path):
            # 디렉토리 이름에서 y_top, y_bottom 추출
            parts = dir_name.split('_')
            y_top = int(parts[-2])
            y_bottom = int(parts[-1].replace('.jpg', ''))

            recognition_results = []
            confidences = []

            # 각 이미지 파일에 대해 OCR 수행
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if file_name.endswith('.jpg'):
                    # 이미지 읽기
                    img = cv2.imread(file_path)
                    if img is not None:
                        # EasyOCR로 OCR 수행
                        ocr_results = reader.readtext(img, detail=1, paragraph=False)
                        
                        # 인식된 텍스트와 신뢰도 추출
                        for result in ocr_results:
                            text, confidence = result[1], result[2]
                            recognition_results.append(text)
                            confidences.append(confidence)

            # 평균 신뢰도 계산
            average_confidence = sum(confidences) / len(confidences) if confidences else 0

            # 결과 처리
            if all(conf >= 0.85 for conf in confidences):
                recognition_result = ''.join(recognition_results)
            else:
                recognition_result = 'out'

            # 결과 리스트에 추가
            results.append({
                'name': dir_name,
                'qn_or_ans': 'qn',
                'y_top': y_top,
                'y_bottom': y_bottom,
                'confident': average_confidence,
                'recognition_result': recognition_result
            })

    # 결과를 DataFrame으로 변환하고 'y_top' 컬럼 기준으로 오름차순 정렬
    df = pd.DataFrame(results)
    df.sort_values(by='y_top', inplace=True)
    return df

def recognizing_answer(answer_path):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=True,
                    model_storage_directory='model',
                    user_network_directory='user_network',
                    recog_network='custom')

    # 결과를 저장할 리스트
    results = []

    # 각 디렉토리 순회
    for dir_name in os.listdir(answer_path):
        dir_path = os.path.join(answer_path, dir_name)
        if os.path.isdir(dir_path):
            # 디렉토리 이름에서 y_top, y_bottom 추출
            parts = dir_name.split('_')
            y_top = int(parts[-2])
            y_bottom = int(parts[-1].replace('.jpg', ''))

            recognition_results = []
            confidences = []

            # 각 이미지 파일에 대해 OCR 수행
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if file_name.endswith('.jpg'):
                    # 이미지 읽기
                    img = cv2.imread(file_path)
                    if img is not None:
                        # EasyOCR로 OCR 수행
                        ocr_results = reader.readtext(img, detail=1, paragraph=False)
                        
                        # 인식된 텍스트와 신뢰도 추출
                        for result in ocr_results:
                            text, confidence = result[1], result[2]
                            recognition_results.append(text)
                            confidences.append(confidence)

            # 평균 신뢰도 계산
            average_confidence = sum(confidences) / len(confidences) if confidences else 0

            # 결과 처리
            if all(conf >= 0.85 for conf in confidences):
                recognition_result = ''.join(recognition_results)
            else:
                recognition_result = 'out'

            # 결과 리스트에 추가
            results.append({
                'name': dir_name,
                'qn_or_ans': 'ans',
                'y_top': y_top,
                'y_bottom': y_bottom,
                'confident': average_confidence,
                'recognition_result': recognition_result
            })

    # 결과를 DataFrame으로 변환하고 'y_top' 컬럼 기준으로 오름차순 정렬
    df = pd.DataFrame(results)
    df.sort_values(by='y_top', inplace=True)
    return df

# 사용 예시
df_question_number = recognizing_question_number('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/question_number')
df_question_number.to_csv('recognition_results.csv', index=False)

df_answer = recognizing_answer('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/answer')
df_answer.to_csv('recognition_results_answer.csv', index=False)