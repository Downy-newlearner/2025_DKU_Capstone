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

    # 각 이미지 파일에 대해 OCR 수행
    for image_path in image_paths:
        # 이미지 읽기
        img = cv2.imread(image_path)
        if img is not None:
            # EasyOCR로 OCR 수행
            ocr_results = reader.readtext(img, detail=1, paragraph=False)

            # 인식된 텍스트와 신뢰도 추출
            recognition_results = []
            confidences = []
            for result in ocr_results:
                text, confidence = result[1], result[2]
                recognition_results.append(text)
                confidences.append(confidence)

            # 평균 신뢰도 계산
            average_confidence = sum(confidences) / len(confidences) if confidences else 0

            # 결과 처리
            recognition_result = ''.join(recognition_results) if all(conf >= 0.85 for conf in confidences) else 'out'

            # 결과 리스트에 추가
            results.append({
                'qn_or_ans': 'qn' if 'question_number' in image_path else 'ans',
                'y_top': 0,  # y_top과 y_bottom은 이미지의 실제 위치에 따라 조정 필요
                'y_bottom': img.shape[0],
                'confident': round(average_confidence, 3),
                'recognition_result': recognition_result
            })

    # 결과를 DataFrame으로 변환
    df = pd.DataFrame(results)
    return df

# Example usage
df = perform_ocr_on_half_cropped('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/half_cropped')
df.to_csv('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ready_for_ocr/half_cropped_recognition_results.csv', index=False)
