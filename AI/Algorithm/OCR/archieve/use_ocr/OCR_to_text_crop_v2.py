import os
import cv2
from easyocr import Reader
import pandas as pd


def recognizing_images_v2(image_path, qn_or_ans):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=True,
                model_storage_directory='use_ocr/model',
                user_network_directory='use_ocr/user_network',
                recog_network='custom')

    # 결과를 저장할 리스트
    results = []

    # 각 디렉토리 순회
    for dir_name in os.listdir(image_path):
        dir_path = os.path.join(image_path, dir_name)
        if os.path.isdir(dir_path):
            # 디렉토리 이름에서 y_top, y_bottom, is_merge 추출
            parts = dir_name.split('_')
            y_top = int(parts[-3])
            y_bottom = int(parts[-2])
            is_merge = int(parts[-1])

            recognition_results = []
            confidences = []

            # 각 이미지 파일에 대해 OCR 수행
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if file_name.endswith('.jpg'):
                    # 이미지 읽기
                    img = cv2.imread(file_path)
                    if img is not None:
                        if is_merge == 1:
                            # digit 별로 자르기
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            _, thresh = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV)
                            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                            # 컨투어 정렬: x_center 기준 오름차순 정렬
                            # 바운딩박스로 변환 후 바운딩 박스 정렬
                            bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
                            bounding_boxes = sorted(bounding_boxes, key=lambda x: x[0])

                            recognition_results = []
                            for bounding_box in bounding_boxes:
                                x, y, w, h = bounding_box
                                digit_img = img[y:y+h, x:x+w]
                                ocr_results = reader.readtext(digit_img, detail=1, paragraph=False)
                                for result in ocr_results:
                                    text, confidence = result[1], result[2]
                                    recognition_results.append(text)
                                    confidences.append(confidence)
                        else:
                            # 기본 OCR 수행
                            ocr_results = reader.readtext(img, detail=1, paragraph=False)
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
                'qn_or_ans': qn_or_ans,
                'y_top': y_top,
                'y_bottom': y_bottom,
                'confident': average_confidence,
                'recognition_result': recognition_result
            })

    # 결과를 DataFrame으로 변환하고 'y_top' 컬럼 기준으로 오름차순 정렬
    df = pd.DataFrame(results)
    df.sort_values(by='y_top', inplace=True)
    return df


if __name__ == "__main__":
    df_question_number = recognizing_images_v2('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/question_number', 'qn')
    df_question_number.to_csv('use_ocr/ocr_results/question_number_v2.csv', index=False)

    df_answer = recognizing_images_v2('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/answer', 'ans')
    df_answer.to_csv('use_ocr/ocr_results/answer_v2.csv', index=False) 