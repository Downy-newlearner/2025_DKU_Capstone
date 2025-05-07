'''

Written by 정다훈 (2025.05.02)

이 파일의 함수들을 이용하여 하고자하는 큰 목표는 다음과 같다.

1. Text crop 이미지 뭉치를 넣으면 이미지 뭉치에 대한 인식 결과 csv 파일을 만든다.
2. 이 csv 파일은 다음과 같이 구성된다.
    - name: 이미지 파일명
    - confident: 인식 결과의 신뢰도
    - recognition_result: 인식 결과
        - 인식 결과의 데이터 종류는 다음과 같다.
            - 인식 성공(인식 결과가 값으로 표시됨)
            - 인식 실패('JSON' 이라는 문자열로 표시됨)

'''

import cv2
from transformers import pipeline
from PIL import Image
import pandas as pd
import os
import json

# text crop 이미지를 넣으면 bb를 만들어주는 함수
def generate_bounding_boxes_from_text_crop(text_crop_image_path):
    # 이미지 읽기
    image = cv2.imread(text_crop_image_path)
    
    # 그레이스케일로 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 컨투어 찾기
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 바운딩 박스 생성
    bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
    
    return bounding_boxes

# 모델 로드
pipe = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)

# bb들을 이미지로 만들어, 이미지를 인식하는 함수
# image_num은 이미지 파일에서 몇 번째 이미지인지를 나타내는 숫자이다.
def recognize_images_from_bounding_boxes(text_crop_image_path, bounding_boxes, image_num):
    # 이미지 읽기
    image = cv2.imread(text_crop_image_path)

    recognition_results = []

    for (x, y, w, h) in bounding_boxes:
        # 바운딩 박스 영역 잘라내기
        cropped_image = image[y:y+h, x:x+w]
        cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)).convert('RGB')

        # 모델을 사용하여 예측
        predictions = pipe(cropped_pil_image)
        if predictions:
            # 가장 높은 확률의 예측 결과를 사용
            top_prediction = predictions[0]
            text, confidence = top_prediction['label'], top_prediction['score']
            if confidence > 0.85:
                recognition_results.append(((x + w//2, y + h//2), text, image_num))
            else:
                recognition_results.append(((x + w//2, y + h//2), 'JSON', image_num))
                return 
        else:
            recognition_results.append(((x + w//2, y + h//2), 'JSON', image_num))

    # x 좌표 기준으로 정렬
    recognition_results.sort(key=lambda x: x[0][0])

    return recognition_results

# recognition_results는 각 바운딩 박스의 중심점과 인식된 텍스트로 구성된 리스트입니다.
# 각 항목은 ((x_center, y_center), text) 형태로 되어 있으며,
# x_center와 y_center는 바운딩 박스의 중심 좌표를 나타내고,
# text는 인식된 텍스트 또는 'JSON' (인식 실패 시)입니다.

def calculate_euclidean_distance(recognition_results1, recognition_results2):
    distance = 0
    for i in range(len(recognition_results1)):
        distance += ((recognition_results1[i][0][0] - recognition_results2[i][0][0]) ** 2 + (recognition_results1[i][0][1] - recognition_results2[i][0][1]) ** 2) ** 0.5
    return distance






# cropped_datasets/text_crop 폴더는 answer, question_number로 구성된다.
# 이 함수는 answer 폴더를 입력받는다고 가정하고 설계된다.
# 리턴은 pandas dataframe이다. 컬럼명은 다음과 같다.
    # name: 이미지 파일명
    # recognition_result: 인식 결과
    # 인식 결과의 데이터 종류는 다음과 같다.
        # 인식 성공(인식 결과가 값으로 표시됨)
        # 인식 실패('JSON' 이라는 문자열로 표시됨)

def split_and_recognize_single_digits(directory_path):

    # sub_dirs에는 directory_path 내의 모든 파일 및 디렉토리 이름이 리스트로 할당된다.
    sub_dirs = os.listdir(directory_path)
    
    # sub_dirs 리스트는 각 이름의 두 번째 언더스코어('_') 뒤에 있는 숫자를 기준으로 정렬된다.
    sub_dirs.sort(key=lambda x: int(x.split('_')[1]))

    # JSON 파일이 존재하지 않거나 비어 있는 경우 초기화
    json_file_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/JSON/recog_failed.json'
    if not os.path.exists(json_file_path) or os.stat(json_file_path).st_size == 0:
        with open(json_file_path, 'w') as f:
            json.dump({}, f)

    for sub_dir in sub_dirs:
        # sub_dir을 순회하며 하위 이미지 파일들의 경로를 변수에 담는다.
        image_paths = os.listdir(os.path.join(directory_path, sub_dir))

        # image_paths 리스트는 각 이름의 두 번째 언더스코어('_') 뒤에 있는 숫자를 기준으로 정렬된다.
        image_paths.sort(key=lambda x: int(x.split('_')[1]))

        results_about_image = []

        image_num = 1

        for text_crop_image in image_paths:
            

            text_crop_image_path = os.path.join(directory_path, sub_dir, text_crop_image)

            # 바운딩 박스 생성
            bounding_boxes = generate_bounding_boxes_from_text_crop(text_crop_image_path)

            # 인식 결과 생성
            recognition_results = recognize_images_from_bounding_boxes(text_crop_image_path, bounding_boxes, image_num)

            if recognition_results is None:
                # 현재 이미지를 JSON 파일에 append
                with open('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/JSON/recog_failed.json', 'r+') as f:
                    data = json.load(f)
                    if text_crop_image not in data:
                        data[text_crop_image] = []
                        f.seek(0)
                        json.dump(data, f, indent=4)
                continue

            results_about_image.append(recognition_results)

            image_num += 1

        # !!!!!!!!!!!!!!! results_about_image 완성 !!!!!!!!!!!!!!!
        print(f'results_about_image: {results_about_image}')


if __name__ == "__main__":
    split_and_recognize_single_digits("/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop_new/answer")

