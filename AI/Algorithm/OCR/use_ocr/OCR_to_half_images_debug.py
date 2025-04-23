'''

Written by 정다훈 2025.04.13
half_cropped 폴더 안에 있는 이미지들에 OCR을 수행하고, 결과를 저장하는 프로그램

'''


import os
import cv2
from easyocr import Reader
import pandas as pd

def perform_ocr_on_half_cropped(input_dir):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=True,
                    model_storage_directory='model',
                    user_network_directory='user_network',
                    recog_network='custom')

    # 결과를 저장할 리스트
    results = []

    # input_dir를 os walk로 순회
    image_paths = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.jpeg', '.jpg', '.png')):
                image_paths.append(os.path.join(root, file))

    # 결과 이미지를 저장할 디렉토리 생성
    result_dir = os.path.join(input_dir, 'ocr_results')
    os.makedirs(result_dir, exist_ok=True)

    # 각 이미지 파일에 대해 OCR 수행
    for image_path in image_paths:
        # 이미지 읽기
        img = cv2.imread(image_path)
        if img is not None:
            # EasyOCR로 OCR 수행
            ocr_results = reader.readtext(img, detail=1, paragraph=False)

            # 각 인식 결과에 대해 처리
            for result in ocr_results:
                bbox, text, confidence = result
                (top_left, top_right, bottom_right, bottom_left) = bbox
                top_left = tuple(map(int, top_left))
                bottom_right = tuple(map(int, bottom_right))

                # 바운딩 박스 그리기
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

                # 텍스트 그리기
                cv2.putText(img, text, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 결과 리스트에 추가
                results.append({
                    'qn_or_ans': 'qn' if 'question_number' in image_path else 'ans',
                    'y_top': top_left[1],
                    'y_bottom': bottom_right[1],
                    'confident': round(confidence, 3),
                    'recognition_result': text if confidence >= 0.85 else 'out'
                })

            # 결과 이미지 저장
            result_image_path = os.path.join(result_dir, os.path.basename(image_path))
            cv2.imwrite(result_image_path, img)

    # 결과를 DataFrame으로 변환
    df = pd.DataFrame(results)
    # 'qn_or_ans'와 'y_top'을 기준으로 정렬
    df.sort_values(by=['qn_or_ans', 'y_top'], inplace=True)
    return df

# Example usage
df = perform_ocr_on_half_cropped('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/half_cropped')
df.to_csv('half_cropped_recognition_results.csv', index=False)
