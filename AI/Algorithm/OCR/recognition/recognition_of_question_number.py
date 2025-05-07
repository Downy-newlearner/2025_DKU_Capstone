import os
import cv2
from transformers import pipeline
from PIL import Image

# 모델 로드
pipe = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)

# question_number 이미지를 single digit으로 크롭하고 인식하는 함수
def recognize_question_number(qn_directory_path):
    y_coordinates_dict = {}

    for filename in os.listdir(qn_directory_path):
        if filename.endswith(('.jpeg', '.jpg', '.png')):
            # 파일 경로
            file_path = os.path.join(qn_directory_path, filename)
            
            # 이미지 읽기
            image = cv2.imread(file_path)
            
            # 그레이스케일로 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # 이진화
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # 컨투어 찾기
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 바운딩 박스 생성 및 인식
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cropped_image = image[y:y+h, x:x+w]
                cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)).convert('RGB')

                # 모델을 사용하여 예측
                predictions = pipe(cropped_pil_image)
                if predictions:
                    top_prediction = predictions[0]
                    text, confidence = top_prediction['label'], top_prediction['score']
                    if confidence > 0.85 and text.isdigit():
                        y_coordinates_dict[text] = [y, y + h]

    return y_coordinates_dict

# 예시 사용
# qn_directory_path = '/path/to/question_number_directory'
# y_coordinates = recognize_question_number(qn_directory_path)
# print(y_coordinates)
