'''
이 스크립트는 EasyOCR을 사용하여 텍스트가 잘린 이미지에서 텍스트를 인식하고, 인식된 결과를 텍스트 파일로 저장하며, 시각화된 이미지를 생성하여 저장합니다. 영어와 한국어를 인식할 수 있습니다.
'''

import os
import easyocr
import cv2
import numpy as np

# EasyOCR 리더 초기화
reader = easyocr.Reader(['en', 'ko'])  # 영어와 한국어 인식

# 이미지 경로 설정
base_dir = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop'
answer_dir = os.path.join(base_dir, 'answer')
question_number_dir = os.path.join(base_dir, 'question_number')

# 결과 저장 경로 설정
answer_output_dir = os.path.join(base_dir, 'ocr_results', 'answer')
question_number_output_dir = os.path.join(base_dir, 'ocr_results', 'question_number')
os.makedirs(answer_output_dir, exist_ok=True)
os.makedirs(question_number_output_dir, exist_ok=True)

# 이미지 파일 처리 함수
def process_images(input_dir, output_dir):
    for subdir in os.listdir(input_dir):
        subdir_path = os.path.join(input_dir, subdir)
        if os.path.isdir(subdir_path):
            image_files = [f for f in os.listdir(subdir_path) if f.endswith(('.jpeg', '.jpg', '.png'))]
            for idx, filename in enumerate(image_files, start=1):
                # 파일 경로
                file_path = os.path.join(subdir_path, filename)
                
                # 이미지 읽기
                image = cv2.imread(file_path)
                
                # OCR 실행
                result = reader.readtext(image)
                
                # 결과 저장을 위한 텍스트 파일 경로
                txt_file_path = os.path.join(output_dir, f'{subdir}_{idx}.txt')
                
                # 시각화 이미지 복사
                vis_image = image.copy()
                
                with open(txt_file_path, 'w') as f:
                    for (bbox, text, confidence) in result:
                        # 바운딩 박스 좌표
                        (top_left, top_right, bottom_right, bottom_left) = bbox
                        top_left = tuple(map(int, top_left))
                        bottom_right = tuple(map(int, bottom_right))
                        
                        # 텍스트 파일에 결과 저장
                        f.write(f'Text: {text}, Confidence: {confidence}, BBox: {bbox}\n')
                        
                        # 시각화 이미지에 바운딩 박스와 텍스트 추가
                        cv2.rectangle(vis_image, top_left, bottom_right, (0, 255, 0), 2)
                        cv2.putText(vis_image, text, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
                        cv2.putText(vis_image, f'{confidence:.2f}', (bottom_right[0], bottom_right[1] + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
                
                # 시각화 이미지 저장 경로
                vis_image_path = os.path.join(output_dir, f'{subdir}_{idx}_vis.jpg')
                cv2.imwrite(vis_image_path, vis_image)
                
                print(f"처리 완료: {filename}, 결과 저장: {txt_file_path}, {vis_image_path}")

# answer 디렉토리 처리
process_images(answer_dir, answer_output_dir)

# question_number 디렉토리 처리
process_images(question_number_dir, question_number_output_dir) 