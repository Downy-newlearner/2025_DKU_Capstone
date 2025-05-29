from PIL import Image
import cv2

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

import numpy as np
from typing import List, Tuple, Dict, Any, Optional

# config는 상위 디렉토리 또는 answer_recognition 패키지 레벨에서 가져와야 함
# 현재 digit_recognizer.py는 answer_recognition/recognition/ 안에 위치
from ..config import mnist_recognition_pipeline

# 이 파일의 함수들은 mnist_recognition_pipeline을 사용합니다.

def pil_find_digit_contours_in_text_crop(text_crop_pil: Image.Image, min_contour_area: int = 3) -> List[Tuple[int, int, int, int]]:
    if text_crop_pil.mode == 'RGB':
        cv_image = np.array(text_crop_pil.convert('L'))
    elif text_crop_pil.mode == 'L':
        cv_image = np.array(text_crop_pil)
    else:
        try: cv_image = np.array(text_crop_pil.convert('L'))
        except Exception as e: print(f"Error converting image to L for digit contour finding: {e}"); return []
    _, thresh = cv2.threshold(cv_image, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    digit_bboxes = []
    img_h, img_w = cv_image.shape[:2]
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if cv2.contourArea(contour) < min_contour_area: continue
        if w > img_w * 0.95 or h > img_h * 0.95: continue
        if w == 0 or h == 0: continue
        digit_bboxes.append((x, y, w, h))
    digit_bboxes.sort(key=lambda bbox: bbox[0])
    return digit_bboxes

def pil_recognize_single_digit(digit_image_pil: Image.Image) -> Optional[Dict[str, Any]]: # mnist_pipe 인자 제거, 내부에서 import된 pipeline 사용
    if not mnist_recognition_pipeline: return None
    try:
        if digit_image_pil.width == 0 or digit_image_pil.height == 0: return None
        predictions = mnist_recognition_pipeline(digit_image_pil)
        if predictions and isinstance(predictions, list) and predictions[0]:
            top_prediction = predictions[0]
            if 'label' in top_prediction and 'score' in top_prediction and isinstance(top_prediction['label'], str) and top_prediction['label'].isdigit() and isinstance(top_prediction['score'], float):
                return {'text': top_prediction['label'], 'confidence': float(top_prediction['score'])}
    except Exception as e: print(f"Error during single digit recognition: {e}, image size: {digit_image_pil.size}")
    return None

def pil_recognize_digits_from_bboxes(original_text_crop_pil: Image.Image, digit_bboxes: List[Tuple[int, int, int, int]]) -> List[Dict[str, Any]]: # mnist_pipe 인자 제거
    recognized_digits_list = []
    if not mnist_recognition_pipeline: return [] # mnist_pipe 대신 import된 pipeline 사용
    for i, (x, y, w, h) in enumerate(digit_bboxes):
        if w == 0 or h == 0: continue
        digit_pil_crop = original_text_crop_pil.crop((x, y, x + w, y + h))
        recognition_result = pil_recognize_single_digit(digit_pil_crop) # mnist_pipe 인자 없이 호출
        if recognition_result:
            recognized_digits_list.append({'bbox_in_text_crop': (x, y, w, h), 'text': recognition_result['text'], 'confidence': recognition_result['confidence'], 'center_x_in_text_crop': x + w / 2.0, 'center_y_in_text_crop': y + h / 2.0})
    recognized_digits_list.sort(key=lambda d: d['center_x_in_text_crop'])
    return recognized_digits_list

def calculate_distance_between_digits_global(digit1_info: Dict[str, Any], digit2_info: Dict[str, Any]) -> float:
    digit1_right_edge = digit1_info['global_x_center'] + (digit1_info['digit_width'] / 2.0)
    digit2_left_edge = digit2_info['global_x_center'] - (digit2_info['digit_width'] / 2.0)
    return max(0.0, digit2_left_edge - digit1_right_edge)

def group_and_combine_digits(globally_sorted_digits: List[Dict[str, Any]], max_spacing_threshold: float, expected_answer_count: int) -> List[str]:
    if not globally_sorted_digits: return []
    combined_numbers_str: List[str] = []
    current_number_str = globally_sorted_digits[0]['text']
    last_digit_info_in_current_number = globally_sorted_digits[0]
    for i in range(1, len(globally_sorted_digits)):
        current_digit_info = globally_sorted_digits[i]
        distance = calculate_distance_between_digits_global(last_digit_info_in_current_number, current_digit_info)
        if distance <= max_spacing_threshold:
            current_number_str += current_digit_info['text']
        else:
            combined_numbers_str.append(current_number_str)
            current_number_str = current_digit_info['text']
        last_digit_info_in_current_number = current_digit_info
    if current_number_str: combined_numbers_str.append(current_number_str)
    if expected_answer_count > 0 and len(combined_numbers_str) != expected_answer_count:
        print(f"  Warning: Digit combination for QN resulted in {len(combined_numbers_str)} numbers, but expected {expected_answer_count}. Result: {combined_numbers_str}")
        if len(combined_numbers_str) > expected_answer_count and expected_answer_count == 1:
            merged_all = "".join(d['text'] for d in globally_sorted_digits)
            print(f"  Attempting to merge all digits to '{merged_all}' due to expected_answer_count=1.")
            return [merged_all]
        elif len(combined_numbers_str) == 1 and expected_answer_count > 1 and len(combined_numbers_str[0]) == expected_answer_count:
            print(f"  Attempting to split '{combined_numbers_str[0]}' into {expected_answer_count} individual digits.")
            return list(combined_numbers_str[0])
    return combined_numbers_str 