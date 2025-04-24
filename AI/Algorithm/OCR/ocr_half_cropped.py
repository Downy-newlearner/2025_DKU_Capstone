import os
import easyocr
import cv2
import numpy as np
import pandas as pd
from pathlib import Path

# EasyOCR 리더 초기화
reader = easyocr.Reader(['en', 'ko'])  # 영어와 한국어 인식

# 이미지 경로 설정
input_dir = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/half_cropped'
output_dir = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR'

# 결과를 저장할 데이터프레임 초기화
answer_results = []
qn_results = []

# 이미지 파일 처리
for filename in os.listdir(input_dir):
    if filename.endswith(('.jpeg', '.jpg', '.png')):
        # 파일 경로
        file_path = os.path.join(input_dir, filename)
        
        # 이미지 읽기
        image = cv2.imread(file_path)
        
        # OCR 실행
        result = reader.readtext(image)
        
        # 결과 처리
        image_name = filename
        recognized_text = ' '.join([text[1] for text in result])
        confidence = np.mean([text[2] for text in result]) if result else 0
        
        # 데이터프레임에 결과 추가
        if 'answer' in filename:
            answer_results.append({
                'image_name': image_name,
                'recognized_text': recognized_text,
                'confidence': confidence
            })
        elif 'question_number' in filename:
            qn_results.append({
                'image_name': image_name,
                'recognized_text': recognized_text,
                'confidence': confidence
            })
        
        print(f"처리 완료: {filename}")

# 결과를 데이터프레임으로 변환
answer_df = pd.DataFrame(answer_results)
qn_df = pd.DataFrame(qn_results)

# 결과 저장 디렉토리 생성
output_path = os.path.join(output_dir, 'ocr_results', 'half_cropped')
os.makedirs(output_path, exist_ok=True)

# CSV 파일로 결과 저장
answer_df.to_csv(os.path.join(output_path, 'answer.csv'), index=False)
qn_df.to_csv(os.path.join(output_path, 'question_number.csv'), index=False)

print(f"인식 결과가 {output_path} 폴더에 저장되었습니다.") 