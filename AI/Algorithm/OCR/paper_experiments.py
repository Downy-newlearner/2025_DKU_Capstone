'''
Written by 정다훈 250418

전처리 종류: Ours / None

모델: EasyOCR_default

총 2개의 실험을 진행한다.
이미지 전처리 결과를 선택 -> OCR 모델 추론 -> 결과를 이미지로 출력(원본 이미지에 bb, 추론 결과 표시)

1. EasyOCR_default / Ours
2. EasyOCR_default / None
'''

import easyocr
import cv2
import pandas as pd
import os
import numpy as np
from pathlib import Path
import glob

# 기본 경로 설정
BASE_DIR = Path('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR')
HALF_CROPPED_DIR = BASE_DIR / "cropped_datasets" / "half_cropped"
TEXT_CROPPED_DIR = BASE_DIR / "cropped_datasets" / "text_crop"
ORIGINAL_DIR = BASE_DIR / "cropped_datasets" / "original_data"
RESULT_DIR = BASE_DIR / "experiments_results"
VISUALIZATION_DIR = RESULT_DIR / "visualization"

def ensure_dir(directory):
    """디렉토리가 존재하지 않으면 생성"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def run_easyocr(image_path, lang_list=['en']):
    """EasyOCR로 이미지 처리"""
    reader = easyocr.Reader(lang_list)
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"이미지를 불러올 수 없습니다: {image_path}")
    result = reader.readtext(image)
    return image, result

def visualize_results(image, result, output_path):
    """OCR 결과를 이미지에 시각화하고 저장"""
    vis_image = image.copy()
    for detection in result:
        top_left = tuple(map(int, detection[0][0]))
        bottom_right = tuple(map(int, detection[0][2]))
        text = detection[1]
        confidence = detection[2]
        
        # 바운딩 박스 그리기
        cv2.rectangle(vis_image, top_left, bottom_right, (0, 0, 255), 2)
        
        # 텍스트와 신뢰도 표시
        text_with_conf = f"{text} ({confidence:.2f})"
        cv2.putText(vis_image, text_with_conf, (top_left[0], top_left[1] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    ensure_dir(os.path.dirname(output_path))
    cv2.imwrite(str(output_path), vis_image)
    print(f"결과 이미지가 저장되었습니다: {output_path}")
    return vis_image

def match_results(half_crop_results, text_crop_results):
    """half crop과 text crop 결과를 비교하고 일치하는 결과를 반환"""
    matched_results = []
    
    # 간단한 매칭 로직 (텍스트 기반)
    for half_result in half_crop_results:
        half_text = half_result[1].lower()
        for text_result in text_crop_results:
            text_crop_text = text_result[1].lower()
            
            # 텍스트가 일치하거나 포함관계인 경우
            if half_text == text_crop_text or half_text in text_crop_text or text_crop_text in half_text:
                # 신뢰도가 더 높은 결과 선택
                if half_result[2] >= text_result[2]:
                    matched_results.append(half_result)
                else:
                    matched_results.append(text_result)
                break
        else:
            # 매칭되는 결과가 없으면 half crop 결과 사용
            matched_results.append(half_result)
    
    # text crop에서 추가된 결과도 포함
    for text_result in text_crop_results:
        text_crop_text = text_result[1].lower()
        if not any(text_crop_text == result[1].lower() or 
                  text_crop_text in result[1].lower() or 
                  result[1].lower() in text_crop_text 
                  for result in matched_results):
            matched_results.append(text_result)
    
    return matched_results

# 1. EasyOCR_default / Ours
def easyocr_default_ours():
    """Ours 전처리 방식으로 OCR 수행"""
    ensure_dir(VISUALIZATION_DIR)
    
    # 1. 전처리 이미지 불러오기(half crop, text crop)
    half_crop_files = glob.glob(str(HALF_CROPPED_DIR / "*.jp*g"))
    text_crop_files = glob.glob(str(TEXT_CROPPED_DIR / "*.jp*g"))
    
    results = {}
    
    for half_file in half_crop_files:
        file_name = os.path.basename(half_file)
        print(f"처리 중: {file_name}")
        
        # half crop 이미지 처리
        half_image, half_results = run_easyocr(half_file)
        half_output_path = VISUALIZATION_DIR / f"half_crop_{file_name}"
        visualize_results(half_image, half_results, half_output_path)

        # text crop 이미지 처리
        
        
        # 같은 이름의 text crop 이미지 찾기
        matching_text_files = [f for f in text_crop_files if os.path.basename(f) == file_name]
        
        if matching_text_files:
            text_file = matching_text_files[0]
            text_image, text_results = run_easyocr(text_file)
            text_output_path = VISUALIZATION_DIR / f"text_crop_{file_name}"
            visualize_results(text_image, text_results, text_output_path)
            
            # 3. match and compare
            matched_results = match_results(half_results, text_results)
            
            # Ours 결과 시각화
            original_image = half_image.copy()  # 원본 이미지로 사용
            ours_output_path = VISUALIZATION_DIR / f"ours_{file_name}"
            visualize_results(original_image, matched_results, ours_output_path)
            
            results[file_name] = {
                'half_crop': half_results,
                'text_crop': text_results,
                'matched': matched_results
            }
        else:
            print(f"Warning: {file_name}에 대한 text crop 이미지를 찾을 수 없습니다.")
            results[file_name] = {
                'half_crop': half_results,
                'text_crop': [],
                'matched': half_results
            }
    
    return results

# 2. EasyOCR_default / None
def easyocr_default_none():
    """전처리 없이 원본 이미지에 OCR 수행"""
    ensure_dir(VISUALIZATION_DIR)
    
    # 1. 전처리 이미지 불러오기(original)
    original_files = glob.glob(str(ORIGINAL_DIR / "*.jp*g"))
    
    results = {}
    
    for orig_file in original_files:
        file_name = os.path.basename(orig_file)
        print(f"처리 중: {file_name}")
        
        # 2. 추론 결과 시각화 후 저장
        orig_image, orig_results = run_easyocr(orig_file)
        output_path = VISUALIZATION_DIR / f"original_{file_name}"
        visualize_results(orig_image, orig_results, output_path)
        
        results[file_name] = orig_results
    
    return results

def run_experiments():
    """모든 실험 실행"""
    print("실험 1: EasyOCR_default / Ours 시작")
    ours_results = easyocr_default_ours()
    
    print("실험 2: EasyOCR_default / None 시작")
    none_results = easyocr_default_none()
    
    print("모든 실험이 완료되었습니다.")
    return ours_results, none_results

if __name__ == "__main__":
    run_experiments()







