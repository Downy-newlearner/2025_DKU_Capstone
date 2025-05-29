from PIL import Image, ImageDraw
import cv2
import numpy as np
# from ultralytics import YOLO # 삭제
import os
import json
from pathlib import Path
import shutil
from typing import Dict, List, Any, Tuple, Optional, TypedDict
# from transformers import pipeline # 삭제
# import re # 삭제

# config.py로부터 import
from .config import (
    YOLO_MODEL_PATH, YOLO_CLASS_QN, YOLO_CLASS_ANS, 
    yolo_model, mnist_recognition_pipeline, KEY_PARSING_REGEX
)

# data_structures.py로부터 import
from .data_structures import DetectedArea

# preprocessing/yolo_detector.py로부터 import
from .preprocessing.yolo_detector import yolo_predict_and_extract_areas_pil

# preprocessing/image_utils.py로부터 import
from .preprocessing.image_utils import (
    enhance_and_find_contours_for_lines,
    crop_between_lines,
    preprocess_line_image_for_text_contours,
    merge_contours_and_crop_text_pil
)

# recognition/digit_recognizer.py로부터 import
from .recognition.digit_recognizer import (
    pil_find_digit_contours_in_text_crop,
    pil_recognize_digits_from_bboxes,
    group_and_combine_digits
)

# utils/key_utils.py로부터 import
from .utils.key_utils import (
    create_question_info_dict,
    generate_final_key_for_ans_crop
)

# --- Configuration --- # 삭제 시작
# YOLO_MODEL_PATH = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/answer_recognition/preprocessing/yolov10_model/best.pt'
# YOLO_CLASS_QN = 0
# YOLO_CLASS_ANS = 1 # 삭제 끝

# --- Global Model Loaders --- # 삭제 시작
# yolo_model = None
# try:
#     if Path(YOLO_MODEL_PATH).exists():
#         yolo_model = YOLO(YOLO_MODEL_PATH)
#         print(f"YOLO model loaded successfully from {YOLO_MODEL_PATH}")
#     else:
#         print(f"YOLO model file not found at {YOLO_MODEL_PATH}")
# except Exception as e:
#     print(f"Error loading YOLO model: {e}")
#     yolo_model = None
# 
# mnist_recognition_pipeline = None
# try:
#     mnist_recognition_pipeline = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)
#     print("MNIST digit recognition model loaded successfully.")
# except Exception as e:
#     print(f"Error loading MNIST digit recognition model: {e}")
#     mnist_recognition_pipeline = None # 삭제 끝

# --- Regex for Key Parsing --- # 삭제 시작
# # 키 형식: "{과목명}_{학번}_{ansAreaID}_L{LineID}_x{xVAL}_qn{QN_STR_WITH_HYPHEN}_ac{ACVAL}(_dupN)?"
# # 예: "Math_12345678_ansArea0_L0_x75_qn1-1_ac2"
# # 예: "Science_87654321_ansArea1_L2_x100_qn10_ac1_dup1"
# KEY_PARSING_REGEX = re.compile(
#     r"^(?P<subject_student_id_base>.+?)"  # 1. 과목명_학번 (non-greedy)
#     r"_(?P<ans_area_id>[a-zA-Z0-9]+)"     # 2. ansArea ID (e.g., ansArea0) - Not captured by name if not needed for grouping
#     r"_L(?P<line_id>[a-zA-Z0-9]+)"        # 3. Line ID (e.g., L1) - Not captured by name
#     r"_x(?P<x_val>\d+)"                   # 4. x_val (digits)
#     r"_qn(?P<qn_str>[a-zA-Z0-9\-]+)"      # 5. qn_str (alphanumeric with hyphen)
#     r"_ac(?P<ac_val>\d+)"                 # 6. ac_val (digits)
#     r"(?:_dup\d+)?$"                      # 7. Optional _dupN suffix
# ) # 삭제 끝

# --- Helper Functions ---

# --- Main Preprocessing Function ---
def preprocess_answer_sheet(
    original_image_path: str,
    answer_key_json_path: str,
) -> Dict[str, Image.Image]:
    final_ans_text_crop_dict: Dict[str, Image.Image] = {}
    if not Path(original_image_path).exists() or not Path(answer_key_json_path).exists():
        print(f"Error: Missing original image or answer key JSON. Image: {original_image_path}, Key: {answer_key_json_path}")
        return {}

    try:
        original_pil_image = Image.open(original_image_path).convert("RGB")
        with open(answer_key_json_path, 'r', encoding='utf-8') as f:
            answer_key_data = json.load(f)
    except Exception as e:
        print(f"Error opening files for preprocessing: {e}")
        return {}
        
    subject_name = Path(original_image_path).parent.name # 과목명 (상위 디렉토리명)
    student_id_filename_stem = Path(original_image_path).stem # 학번 (파일명에서 확장자 제외)
    subject_student_id_base = f"{subject_name}_{student_id_filename_stem}"
    
    print(f"Preprocessing: {subject_student_id_base} (from {original_image_path})")

    print("  Step 1: YOLO detection...")
    qn_detected_areas, ans_detected_areas = yolo_predict_and_extract_areas_pil(original_pil_image, subject_student_id_base)

    if not ans_detected_areas: print(f"  No ANS areas by YOLO for {subject_student_id_base}."); return {}
    if not qn_detected_areas: print(f"  No QN areas by YOLO for {subject_student_id_base}."); return {}
    
    print("  Step 2&3 (QN Processing for question_info_dict)...")
    # _create_question_info_dict는 이제 qn_detected_areas를 직접 사용
    question_info_dict = create_question_info_dict(qn_detected_areas, answer_key_data)
    if not question_info_dict: 
        print(f"  Failed to create question_info_dict for {subject_student_id_base}. Check QN detection and answer key matching."); 
        return {}

    print("  Step 4 & 5 (ANS Processing & Key Generation)...")
    for ans_area_idx, ans_area_data in enumerate(ans_detected_areas):
        ans_area_pil = ans_area_data['image_obj']
        ans_area_y_offset_orig = ans_area_data['bbox'][1]
        current_ans_area_id = f"ansArea{ans_area_idx}" # DetectedArea에 id가 없으므로 인덱스 사용

        line_contours = enhance_and_find_contours_for_lines(ans_area_pil)
        line_cropped_ans_list = crop_between_lines(ans_area_pil, line_contours)

        for line_idx, line_crop_data in enumerate(line_cropped_ans_list):
            line_ans_pil = line_crop_data['image_obj']
            line_y_top_in_ans_area = line_crop_data['y_top_in_area']
            current_line_id = f"L{line_idx}"

            text_contours_cv = preprocess_line_image_for_text_contours(line_ans_pil)
            final_ans_text_crops_in_line = merge_contours_and_crop_text_pil(line_ans_pil, text_contours_cv)
            
            for text_crop_data_in_line in final_ans_text_crops_in_line:
                ans_text_crop_pil = text_crop_data_in_line['image_obj']
                ans_text_crop_full_info = {
                    'image_obj': ans_text_crop_pil,
                    'x_in_line': text_crop_data_in_line['x_in_line'],
                    'y_in_line_relative_to_line_crop_top': text_crop_data_in_line['y_in_line'],
                    'line_y_top_relative_to_ans_area': line_y_top_in_ans_area,
                    'ans_area_y_offset_orig': ans_area_y_offset_orig,
                    'ans_area_id': current_ans_area_id,
                    'line_id_in_ans_area': current_line_id
                }
                final_key_base = generate_final_key_for_ans_crop(
                    subject_student_id_base, # 과목명_학번 전달
                    ans_text_crop_full_info,
                    question_info_dict,
                    answer_key_data
                )
                temp_key = final_key_base
                key_suffix = 0
                while temp_key in final_ans_text_crop_dict:
                    key_suffix += 1
                    temp_key = f"{final_key_base}_dup{key_suffix}"
                final_key = temp_key
                final_ans_text_crop_dict[final_key] = ans_text_crop_pil
    
    print(f"  Preprocessing finished: {subject_student_id_base}. Found {len(final_ans_text_crop_dict)} ans_text_crops.")
    return final_ans_text_crop_dict

# --- Main Recognition Function (UPDATED) ---
def recognize_answer_sheet_data(
    processed_ans_crops: Dict[str, Image.Image], 
    answer_key_data: Dict[str, Any]
) -> Dict[str, Any]:
    print(f"Recognition started for {len(processed_ans_crops)} ans_text_crop objects.")
    grouped_for_recognition: Dict[Tuple[str, str], List[Dict[str,Any]]] = {}

    for full_key, img_obj in processed_ans_crops.items():
        match = KEY_PARSING_REGEX.match(full_key)
        if not match:
            print(f"  Error: Key '{full_key}' did not match expected pattern. Skipping.")
            continue
        
        parsed_key_data = match.groupdict()
        subject_student_id_base = parsed_key_data['subject_student_id_base']
        qn_str = parsed_key_data['qn_str'] # 하이픈 포함 가능
        ac_val = int(parsed_key_data['ac_val'])
        x_val = int(parsed_key_data['x_val'])
            
        group_key = (subject_student_id_base, qn_str) # 그룹핑 키: (과목명_학번, 문제번호)
        if group_key not in grouped_for_recognition:
            grouped_for_recognition[group_key] = []
        
        grouped_for_recognition[group_key].append({
            'full_key': full_key, 
            'image_obj': img_obj,
            'x_coord_of_text_crop_in_line': x_val, 
            'expected_answer_count': ac_val
        })
            
    recognition_results_by_sheet_and_qn: Dict[str, Dict[str, Any]] = {}

    if not mnist_recognition_pipeline:
        print("MNIST model not loaded. Cannot perform recognition.")
        for (subject_student_id, qn_str_key), _ in grouped_for_recognition.items():
            if subject_student_id not in recognition_results_by_sheet_and_qn:
                recognition_results_by_sheet_and_qn[subject_student_id] = {}
            recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'failure', 'reason': 'MNIST model not available'}
    else:
        for (subject_student_id, qn_str_key), crop_infos_for_qn_list in grouped_for_recognition.items():
            if subject_student_id not in recognition_results_by_sheet_and_qn:
                recognition_results_by_sheet_and_qn[subject_student_id] = {}

            sorted_text_crops_for_qn = sorted(crop_infos_for_qn_list, key=lambda x: x['x_coord_of_text_crop_in_line'])
            all_recognized_digits_for_this_qn_globally_sorted: List[Dict[str, Any]] = []
            
            for text_crop_data in sorted_text_crops_for_qn:
                current_text_crop_pil = text_crop_data['image_obj']
                x_offset_of_this_text_crop = text_crop_data['x_coord_of_text_crop_in_line']
                digit_bboxes_in_current_text_crop = pil_find_digit_contours_in_text_crop(current_text_crop_pil, min_contour_area=3)
                if not digit_bboxes_in_current_text_crop: continue
                recognized_digits_within_this_text_crop = pil_recognize_digits_from_bboxes(current_text_crop_pil, digit_bboxes_in_current_text_crop)
                for r_digit_info in recognized_digits_within_this_text_crop:
                    all_recognized_digits_for_this_qn_globally_sorted.append({'text': r_digit_info['text'], 'confidence': r_digit_info['confidence'], 'global_x_center': x_offset_of_this_text_crop + r_digit_info['center_x_in_text_crop'], 'digit_width': r_digit_info['bbox_in_text_crop'][2]})

            current_qn_status = "success"
            reason_for_failure = "Unknown"

            if not all_recognized_digits_for_this_qn_globally_sorted:
                current_qn_status = "failure"; reason_for_failure = "No digits recognized for this QN"
            else:
                all_recognized_digits_for_this_qn_globally_sorted.sort(key=lambda d: d['global_x_center'])
                num_expected_answers = sorted_text_crops_for_qn[0]['expected_answer_count'] if sorted_text_crops_for_qn else 0
                avg_digit_width = np.mean([d['digit_width'] for d in all_recognized_digits_for_this_qn_globally_sorted if d['digit_width'] > 0]) if any(d['digit_width'] > 0 for d in all_recognized_digits_for_this_qn_globally_sorted) else 10
                dynamic_spacing_threshold = max(5.0, avg_digit_width * 0.75)
                final_answer_strings = group_and_combine_digits(all_recognized_digits_for_this_qn_globally_sorted, max_spacing_threshold=dynamic_spacing_threshold, expected_answer_count=num_expected_answers)
                if not final_answer_strings:
                    current_qn_status = "failure"; reason_for_failure = "Digit combination resulted in no answer strings"
                else:
                    recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'success', 'recognized_answers': final_answer_strings}
            
            if current_qn_status == "failure":
                 recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'failure', 'reason': reason_for_failure}

    final_success_json = {}
    final_failure_json = {}
    for subject_student_id_base, qn_results_map in recognition_results_by_sheet_and_qn.items():
        sheet_all_success = True; sheet_answers = {}; sheet_failures = {}; has_any_qn_data = False
        for qn, result in qn_results_map.items():
            has_any_qn_data = True
            if result['status'] == 'success':
                sheet_answers[qn] = result['recognized_answers']
            else:
                sheet_all_success = False
                # 'all_recognized_digits_for_this_qn_globally_sorted' is not in scope here for failure details
                # We might need to pass it or store it if detailed logging per qn is needed for failures
                sheet_failures[qn] = {'reason': result.get('reason', 'Unknown failure')}
        
        if not has_any_qn_data and subject_student_id_base not in final_failure_json:
            final_failure_json[subject_student_id_base] = {"reason": f"No questions processed or recognized for this sheet {subject_student_id_base}."}
            continue

        if sheet_answers:
            final_success_json[subject_student_id_base] = sheet_answers
            if not sheet_all_success and sheet_failures:
                 if subject_student_id_base not in final_failure_json: final_failure_json[subject_student_id_base] = {}
                 final_failure_json[subject_student_id_base].update({"partial_failures": sheet_failures})
        elif sheet_failures:
            final_failure_json[subject_student_id_base] = {"overall_status": "complete_failure", "details": sheet_failures}

    print(f"  Recognition finished. Success entries: {len(final_success_json)}, Failure entries: {len(final_failure_json)}")
    return {"success_json": final_success_json, "failure_json": final_failure_json}

if __name__ == "__main__":
    # 테스트 실행을 위한 설정
    # 중요: 이 테스트는 answer_recognition 디렉토리 외부 (예: AI 디렉토리)에서 
    # python -m answer_recognition.main 으로 실행해야 상대경로 import가 정상 동작합니다.
    # 또는, 아래 경로들을 절대경로로 명시하거나, 테스트 환경에 맞게 조정해야 합니다.

    # 사용자가 제공한 테스트 파일 경로
    test_image_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer/32174515.jpg'
    test_answer_key_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer.json'

    print(f"--- Starting Test for {test_image_path} ---")

    # 1. 전처리 단계 실행
    print("\n--- Running Preprocessing ---")
    processed_crops = preprocess_answer_sheet(test_image_path, test_answer_key_path)

    if not processed_crops:
        print("Preprocessing returned no crops. Test will not proceed to recognition.")
    else:
        print(f"\nPreprocessing finished. Number of cropped answer areas: {len(processed_crops)}")
        # 전처리 결과 (키와 이미지 크기 정도만) 간단히 출력
        # for key, img in processed_crops.items():
        #     print(f"  Key: {key}, Image Size: {img.size}")

        # 2. 인식 단계 실행
        print("\n--- Running Recognition ---")
        # answer_key_data를 다시 로드해야 할 수 있으므로, 여기서는 answer_key_json_path를 사용
        # 또는 preprocess_answer_sheet에서 answer_key_data도 함께 반환하도록 수정할 수 있음.
        # 현재 recognize_answer_sheet_data는 answer_key_data 자체를 받으므로, json파일을 다시 로드합니다.
        try:
            with open(test_answer_key_path, 'r', encoding='utf-8') as f:
                ans_key_data_for_rec = json.load(f)
            
            recognition_results = recognize_answer_sheet_data(processed_crops, ans_key_data_for_rec)

            print("\n--- Recognition Results ---")
            print("Success JSON:")
            print(json.dumps(recognition_results.get("success_json", {}), indent=2, ensure_ascii=False))
            print("\nFailure JSON:")
            print(json.dumps(recognition_results.get("failure_json", {}), indent=2, ensure_ascii=False))

        except FileNotFoundError:
            print(f"Error: Answer key file not found at {test_answer_key_path} for recognition step.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {test_answer_key_path}.")
        except Exception as e:
            print(f"An unexpected error occurred during recognition: {e}")

    print("\n--- Test Finished ---")
