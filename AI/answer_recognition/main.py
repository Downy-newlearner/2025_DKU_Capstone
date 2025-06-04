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
import re # 삭제

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

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

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

    print("  단계 1: YOLO detection...")
    qn_detected_area, ans_detected_area = yolo_predict_and_extract_areas_pil(original_pil_image, subject_student_id_base)

    if ans_detected_area is None:
        print(f"  답변 영역이 YOLO에서 발견되지 않음 {subject_student_id_base}.")
        return {}
    if qn_detected_area is None:
        print(f"  질문 영역이 YOLO에서 발견되지 않음 {subject_student_id_base}.")
        return {}
    
    print("  단계 2&3 (질문 정보 딕셔너리 생성)...")
    question_info_dict = create_question_info_dict([qn_detected_area], answer_key_data)
    # --- question_info_dict 출력 디버그 코드 시작 ---
    print(f"  [Debug Main] 생성된 question_info_dict (키 개수: {len(question_info_dict)}):")
    # json.dumps를 사용하여 보기 좋게 출력, 한글 깨짐 방지 ensure_ascii=False
    # 너무 길 경우 일부만 출력하거나, 파일로 저장하는 것을 고려할 수 있습니다.
    # 여기서는 전체를 출력합니다.
    try:
        print(json.dumps(question_info_dict, indent=2, ensure_ascii=False))
        print("여깄어요!@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    except TypeError as e:
        # PIL Image 객체 등이 직접 포함되어 json.dumps가 실패하는 경우를 대비
        print(f"    question_info_dict를 JSON으로 변환 중 오류 (직접 출력 시도): {e}")
        print(question_info_dict) # 이 경우, 일반 print로 출력
    # --- question_info_dict 출력 디버그 코드 끝 ---
    if not question_info_dict: 
        print(f"  질문 정보 딕셔너리 생성 실패 {subject_student_id_base}. 질문 발견 및 답변 키 일치 확인 필요.")
        return {}

    print("  단계 4 & 5 (답변 영역 처리 및 키 생성)...") # DEBUG KOR
    ans_area_idx = 0  # 단일 객체이므로 인덱스를 0으로 고정
    
    # ans_area_data 대신 ans_detected_area (단일 객체)를 직접 사용
    ans_area_pil = ans_detected_area['image_obj'] # ans 영역의 PIL 이미지 객체
    ans_area_y_offset_orig = ans_detected_area['bbox'][1] # 원본 답안지 이미지 기준으로 답변 영역의 y 시작 오프셋.
    current_ans_area_id = f"ansArea{ans_area_idx}" # 항상 "ansArea0"

    # 답변 영역 내에서 수평선 윤곽 찾기 및 라인 분리
    line_contours = enhance_and_find_contours_for_lines(ans_area_pil) # 이 함수의 반환 값 (감지된 수평선들의 경계 상자 리스트)이 line_contours에 할당됩니다.
    line_cropped_ans_list = crop_between_lines(ans_area_pil, line_contours)
        # ans_area_pil (답변 영역 이미지)과 line_contours (찾아낸 수평선 정보)가 crop_between_lines 함수의 인자로 전달됩니다.
        # 이 함수의 반환 값 (잘린 각 라인 이미지와 해당 라인의 y좌표 정보를 담은 딕셔너리들의 리스트)이 line_cropped_ans_list에 할당됩니다.

    # 이 루프는 line_cropped_ans_list에 있는 각 라인 조각에 대해 반복됩니다. 
    # line_idx는 현재 라인의 인덱스, line_crop_data는 현재 라인 이미지와 y정보를 담은 딕셔너리입니다.
    for line_idx, line_crop_data in enumerate(line_cropped_ans_list):
        line_ans_pil = line_crop_data['image_obj']
        # # --- line_ans_pil 저장 디버그 코드 시작 ---
        # try:
        #     debug_line_img_dir = Path("debug_line_images")
        #     os.makedirs(debug_line_img_dir, exist_ok=True)
            
        #     # 파일명 생성을 위해 current_line_id를 여기서 임시로 정의 또는 사용
        #     temp_line_id_for_filename = f"L{line_idx}"

        #     safe_subject_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', subject_student_id_base)
        #     safe_ans_area_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', current_ans_area_id) # current_ans_area_id는 이 루프 바깥에서 정의됨
        #     safe_line_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', temp_line_id_for_filename)

        #     line_filename = f"{safe_subject_id}_{safe_ans_area_id}_{safe_line_id}.png"
        #     line_save_path = debug_line_img_dir / line_filename
        #     line_ans_pil.save(line_save_path)
        #     print(f"  [Debug Main] 라인 이미지 저장됨: {line_save_path}")
        # except Exception as e:
        #     print(f"  [Debug Main] 라인 이미지 저장 중 오류: {e}")
        # # --- line_ans_pil 저장 디버그 코드 끝 ---
        line_y_top_in_ans_area = line_crop_data['y_top_in_area']
        current_line_id = f"L{line_idx}" # 실제 current_line_id는 여기서 할당됨 (키 생성 등에 사용)

        # 라인 내 텍스트 컨투어(윤곽선) 검출
        text_contours_cv = preprocess_line_image_for_text_contours(line_ans_pil)
        # 텍스트 컨투어 병합 및 개별 텍스트 이미지 추출
        final_ans_text_crops_in_line = merge_contours_and_crop_text_pil(line_ans_pil, text_contours_cv) # horizontally_crop_image -> text_crop images
        
        # 개별 텍스트 조각(text crop) 처리 루프
        for text_idx, text_crop_data_in_line in enumerate(final_ans_text_crops_in_line):
            ans_text_crop_pil = text_crop_data_in_line['image_obj']
            
            ans_text_crop_full_info = {
                'image_obj': ans_text_crop_pil,  # 최종적으로 잘린 개별 텍스트 조각의 PIL Image 객체
                'x_in_line': text_crop_data_in_line['x_in_line'], # 현재 라인(line_ans_pil) 내에서 이 텍스트 조각의 시작 x 좌표
                'y_in_line_relative_to_line_crop_top': text_crop_data_in_line['y_in_line'], # 현재 라인(line_ans_pil)의 상단 기준으로 이 텍스트 조각의 시작 y 좌표 -> 필요 없어보임
                'line_y_top_relative_to_ans_area': line_y_top_in_ans_area, # 전체 답변 영역(ans_area_pil) 내에서 현재 라인의 시작 y 좌표
                'ans_area_y_offset_orig': ans_area_y_offset_orig, # 원본 답안지 이미지에서 전체 답변 영역(ans_area_pil)의 시작 y 오프셋
                # 'ans_area_id': current_ans_area_id, # 제거됨 (이전에 사용되었던 전체 답변 영역의 ID)
                'line_id_in_ans_area': current_line_id # 현재 라인의 ID (예: "L0", "L1")
            }
            
            final_key_base = generate_final_key_for_ans_crop(
                subject_student_id_base, # 과목명_학번 전달
                ans_text_crop_full_info,
                question_info_dict,
                answer_key_data
            )
            # (여기)
            temp_key = final_key_base
            key_suffix = 0
            while temp_key in final_ans_text_crop_dict:
                key_suffix += 1
                temp_key = f"{final_key_base}_dup{key_suffix}"
            final_key = temp_key
            # --- final_key에 "qnunknownQN" 포함 시 line_ans_pil 이미지 저장 디버그 코드 시작 ---
            if "qnunknownQN" in final_key:
                try:
                    debug_unknown_line_dir = Path("debug_unknown_qn_lines")
                    os.makedirs(debug_unknown_line_dir, exist_ok=True)
                    
                    # final_key를 기반으로 파일명 생성, 라인 이미지임을 명시
                    line_image_filename = f"{final_key}_LINE.png"
                    line_image_save_path = debug_unknown_line_dir / line_image_filename
                    
                    # 현재 루프의 line_ans_pil (해당 텍스트 조각이 속한 전체 라인 이미지) 저장
                    line_ans_pil.save(line_image_save_path)
                    print(f"    [Debug Main] 'unknownQN' 포함 라인 이미지 저장됨: {line_image_save_path}")
                except Exception as e:
                    print(f"    [Debug Main] 'unknownQN' 포함 라인 이미지 저장 중 오류: {e}")
            # --- final_key에 "qnunknownQN" 포함 시 line_ans_pil 이미지 저장 디버그 코드 끝 ---
            final_ans_text_crop_dict[final_key] = ans_text_crop_pil
            # --- ans_text_crop_pil 저장 디버그 코드 시작 ---
            # try:
            #     debug_text_crop_dir = Path("debug_text_crop_images")
            #     os.makedirs(debug_text_crop_dir, exist_ok=True)
                
            #     # final_key를 파일명으로 사용 (특수문자 처리 등은 final_key 생성 시 이미 어느정도 반영되었거나, 필요시 추가)
            #     # 여기서는 final_key가 이미 적절한 문자열이라고 가정
            #     # 만약 final_key에 파일명으로 부적절한 문자가 포함될 가능성이 있다면 re.sub 등으로 처리 필요
            #     text_crop_filename = f"{final_key}.png"
            #     text_crop_save_path = debug_text_crop_dir / text_crop_filename
            #     ans_text_crop_pil.save(text_crop_save_path)
            #     # print(f"    [Debug Main] 텍스트 조각 이미지 저장됨: {text_crop_save_path}") # 너무 많은 로그를 유발할 수 있어 주석 처리
            # except Exception as e:
            #     print(f"    [Debug Main] 텍스트 조각 이미지 저장 중 오류: {e}")
            # # --- ans_text_crop_pil 저장 디버그 코드 끝 ---
    
    print(f"  전처리 완료: {subject_student_id_base}. 총 {len(final_ans_text_crop_dict)}개의 잘린 답변 텍스트 이미지 생성됨.") # DEBUG KOR
    return final_ans_text_crop_dict

# --- Main Recognition Function (UPDATED) ---
def recognize_answer_sheet_data(
    processed_ans_crops: Dict[str, Image.Image],
    answer_key_data: Dict[str, Any] # answer_key_data는 현재 직접 사용되지 않지만, 향후 확장성을 위해 유지될 수 있습니다.
) -> Dict[str, Any]:
    """
    전처리된 답안 텍스트 조각 이미지들로부터 숫자를 인식하여 최종 답안을 생성합니다.

    Args:
        processed_ans_crops: 키(고유 식별자)와 PIL Image 객체(텍스트 조각)를 값으로 가지는 딕셔너리.
        answer_key_data: (현재 직접 사용 X) 원본 답안 키 JSON 데이터. 
                         키 파싱을 통해 얻은 정보(예: answer_count)가 이 데이터에서 비롯됩니다.

    Returns:
        인식 성공 및 실패 정보를 담은 딕셔너리.
        {
            "success_json": { "학번_과목": {"문제번호": ["인식된 답1", "인식된 답2"], ...} ... },
            "failure_json": { "학번_과목": {"문제번호": {"reason": "실패 이유"}, ...} ... }
        }
    """
    print(f"Recognition started for {len(processed_ans_crops)} ans_text_crop objects.")

    # --- 단계 1: 입력 데이터(processed_ans_crops)를 (학번_과목, 문제번호) 기준으로 그룹핑 ---
    # 목적: 동일 문제에 속하는 여러 텍스트 조각들을 함께 처리하기 위함.
    #       예를 들어, "1, 2, 3"과 같이 여러 조각으로 나뉘어 크롭된 답도 하나의 문제로 묶습니다.
    grouped_for_recognition: Dict[Tuple[str, str], List[Dict[str,Any]]] = {}

    for full_key, img_obj in processed_ans_crops.items():
        # full_key 예시: "test_answer_32174515_LlineX_x220_qn1-1_ac1"
        match = KEY_PARSING_REGEX.match(full_key) # 정규표현식을 사용해 키 정보를 파싱합니다.
        if not match:
            print(f"  Error: Key '{full_key}' did not match expected pattern. Skipping.")
            continue

        parsed_key_data = match.groupdict() # 파싱된 결과를 딕셔너리 형태로 가져옵니다.
        subject_student_id_base = parsed_key_data['subject_student_id_base'] # 예: "test_answer_32174515"
        qn_str = parsed_key_data['qn_str'] # 예: "1-1" (하이픈 포함 가능)
        ac_val = int(parsed_key_data['ac_val']) # 예: 1 (해당 문제의 예상 답안 개수)
        x_val = int(parsed_key_data['x_val']) # 예: 220 (라인 내 텍스트 조각의 x 좌표)

        # 그룹핑 키: (과목명_학번, 문제번호) 튜플을 사용합니다.
        group_key = (subject_student_id_base, qn_str)
        if group_key not in grouped_for_recognition:
            grouped_for_recognition[group_key] = []

        # 그룹에 현재 텍스트 조각의 정보(이미지, x좌표, 예상 답안 개수 등)를 추가합니다.
        grouped_for_recognition[group_key].append({
            'full_key': full_key,
            'image_obj': img_obj,
            'x_coord_of_text_crop_in_line': x_val,
            'expected_answer_count': ac_val # 이 값은 digit_recognizer.group_and_combine_digits에서 사용됩니다.
        })

    recognition_results_by_sheet_and_qn: Dict[str, Dict[str, Any]] = {} # 최종 인식 결과를 저장할 딕셔너리

    # --- 단계 2: MNIST 모델 로드 상태 확인 ---
    # 모델이 로드되지 않았으면, 모든 문제에 대해 인식 실패 처리.
    if not mnist_recognition_pipeline:
        print("MNIST model not loaded. Cannot perform recognition.")
        for (subject_student_id, qn_str_key), _ in grouped_for_recognition.items():
            if subject_student_id not in recognition_results_by_sheet_and_qn:
                recognition_results_by_sheet_and_qn[subject_student_id] = {}
            recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'failure', 'reason': 'MNIST model not available'}
    else: # MNIST model is loaded
        # --- 단계 3: 그룹핑된 문제별로 숫자 인식 처리 ---
        for (subject_student_id, qn_str_key), crop_infos_for_qn_list in grouped_for_recognition.items():
            if subject_student_id not in recognition_results_by_sheet_and_qn:
                recognition_results_by_sheet_and_qn[subject_student_id] = {}

            # --- 단계 3-1: 현재 문제에 속한 텍스트 조각들을 x 좌표 기준으로 정렬 ---
            # 답안이 여러 조각으로 나뉘었을 경우, 왼쪽에서 오른쪽 순서로 처리하기 위함입니다.
            sorted_text_crops_for_qn = sorted(crop_infos_for_qn_list, key=lambda x: x['x_coord_of_text_crop_in_line'])

            all_recognized_digits_for_this_qn_globally_sorted: List[Dict[str, Any]] = [] # 현재 문제의 모든 텍스트 조각에서 인식된 숫자 정보를 저장 (전체 문제 영역 기준 x좌표로 정렬 예정)

            # --- 단계 3-2: 정렬된 각 텍스트 조각 이미지에서 숫자 검출 및 인식 ---
            for text_crop_data in sorted_text_crops_for_qn:
                current_text_crop_pil = text_crop_data['image_obj'] # 현재 처리할 텍스트 조각 PIL 이미지
                x_offset_of_this_text_crop = text_crop_data['x_coord_of_text_crop_in_line'] # 라인 내에서 현재 텍스트 조각의 시작 x 좌표

                # --- 단계 3-2-1: 텍스트 조각 내에서 개별 숫자 윤곽선(bounding box) 찾기 ---
                # min_contour_area는 너무 작은 노이즈를 필터링하기 위한 값입니다.
                digit_bboxes_in_current_text_crop = pil_find_digit_contours_in_text_crop(current_text_crop_pil, min_contour_area=3)
                if not digit_bboxes_in_current_text_crop: continue # 숫자가 검출되지 않으면 다음 텍스트 조각으로 넘어감

                # --- 단계 3-2-2: 검출된 각 숫자 윤곽선 영역에 대해 MNIST 모델로 숫자 인식 ---
                recognized_digits_within_this_text_crop = pil_recognize_digits_from_bboxes(current_text_crop_pil, digit_bboxes_in_current_text_crop)

                # 인식된 숫자 정보를 저장. x 좌표는 전체 문제 영역 기준의 'global_x_center'로 변환하여 저장합니다.
                for r_digit_info in recognized_digits_within_this_text_crop:
                    all_recognized_digits_for_this_qn_globally_sorted.append({
                        'text': r_digit_info['text'], # 인식된 숫자 (문자열)
                        'confidence': r_digit_info['confidence'], # 인식 신뢰도
                        'global_x_center': x_offset_of_this_text_crop + r_digit_info['center_x_in_text_crop'], # 문제 라인에서의 전역 x 중심 좌표
                        'digit_width': r_digit_info['bbox_in_text_crop'][2] # 숫자 bounding box의 너비
                    })

            current_qn_status = "success" # 현재 문제의 인식 상태 초기값
            reason_for_failure = "Unknown" # 실패 시 이유

            # --- 단계 3-3: 현재 문제에 대해 인식된 모든 숫자를 종합하여 최종 답안 생성 ---
            if not all_recognized_digits_for_this_qn_globally_sorted:
                # 현재 문제에서 숫자가 전혀 인식되지 않은 경우
                current_qn_status = "failure"; reason_for_failure = "No digits recognized for this QN"
            else:
                # --- 단계 3-3-1: 인식된 숫자들을 전역 x 중심 좌표 기준으로 다시 정렬 ---
                all_recognized_digits_for_this_qn_globally_sorted.sort(key=lambda d: d['global_x_center'])

                # --- 단계 3-3-2: 예상 답안 개수 및 숫자 간 간격 임계값 설정 ---
                # expected_answer_count는 키 파싱 시 얻은 ac_val 값입니다.
                num_expected_answers = sorted_text_crops_for_qn[0]['expected_answer_count'] if sorted_text_crops_for_qn else 0
                # 숫자 너비의 평균을 기준으로 동적 간격 임계값 설정 (숫자들이 너무 붙어있거나 떨어져 있는 경우를 처리)
                avg_digit_width = np.mean([d['digit_width'] for d in all_recognized_digits_for_this_qn_globally_sorted if d['digit_width'] > 0]) if any(d['digit_width'] > 0 for d in all_recognized_digits_for_this_qn_globally_sorted) else 10
                dynamic_spacing_threshold = max(5.0, avg_digit_width * 0.75) # 최소 5픽셀, 또는 평균 너비의 75%

                # --- 단계 3-3-3: 정렬된 숫자 정보를 바탕으로 그룹핑하여 최종 답안 문자열 리스트 생성 ---
                # 예: [ {'text':'1', 'global_x_center':10}, {'text':'2', 'global_x_center':20}, {'text':'3', 'global_x_center':50} ]
                #      -> expected_answer_count=1 이면 ["12", "3"] 또는 ["123"] 등 (간격에 따라)
                #      -> expected_answer_count=2 이고, 답이 "1, 23" 이면 ["1", "23"] 과 같이 그룹핑 시도
                final_answer_strings = group_and_combine_digits(
                    all_recognized_digits_for_this_qn_globally_sorted,
                    max_spacing_threshold=dynamic_spacing_threshold,
                    expected_answer_count=num_expected_answers
                )
                if not final_answer_strings:
                    current_qn_status = "failure"; reason_for_failure = "Digit combination resulted in no answer strings"
                else:
                    # 성공적으로 답안 문자열이 생성된 경우
                    recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'success', 'recognized_answers': final_answer_strings}

            # --- 단계 3-4: 현재 문제 인식 실패 시 결과 저장 ---
            if current_qn_status == "failure":
                 recognition_results_by_sheet_and_qn[subject_student_id][qn_str_key] = {'status': 'failure', 'reason': reason_for_failure}

    # --- 단계 4: 최종 결과 집계 및 반환 형식 구성 ---
    # 인식 결과를 성공(success_json)과 실패(failure_json)로 나누어 구성합니다.
    final_success_json = {}
    final_failure_json = {}
    for subject_student_id_base, qn_results_map in recognition_results_by_sheet_and_qn.items():
        sheet_all_success = True; sheet_answers = {}; sheet_failures = {}; has_any_qn_data = False
        for qn, result in qn_results_map.items():
            has_any_qn_data = True # 해당 답안지에 처리된 문제가 하나라도 있는지 확인
            if result['status'] == 'success':
                sheet_answers[qn] = result['recognized_answers']
            else:
                sheet_all_success = False # 하나라도 실패하면 전체 성공은 아님
                sheet_failures[qn] = {'reason': result.get('reason', 'Unknown failure')}

        # 해당 답안지에 대해 처리된 문제가 전혀 없는 경우 (예: 그룹핑 후 필터링 등)
        if not has_any_qn_data and subject_student_id_base not in final_failure_json:
            final_failure_json[subject_student_id_base] = {"reason": f"No questions processed or recognized for this sheet {subject_student_id_base}."}
            continue

        if sheet_answers: # 성공적으로 인식된 답안이 하나라도 있는 경우
            final_success_json[subject_student_id_base] = sheet_answers
            if not sheet_all_success and sheet_failures: # 부분적으로 실패한 문제가 있는 경우
                 if subject_student_id_base not in final_failure_json: final_failure_json[subject_student_id_base] = {}
                 final_failure_json[subject_student_id_base].update({"partial_failures": sheet_failures})
        elif sheet_failures: # 모든 문제가 실패한 경우
            final_failure_json[subject_student_id_base] = {"overall_status": "complete_failure", "details": sheet_failures}

    print(f"  Recognition finished. Success entries: {len(final_success_json)}, Failure entries: {len(final_failure_json)}")
    return {"success_json": final_success_json, "failure_json": final_failure_json}

if __name__ == "__main__":
    # preprocess_answer_sheet 함수 테스트
    test_original_image_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer/32174515.jpg'
    test_answer_key_json_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer.json'

    print(f"--- Running Preprocessing Test for {test_original_image_path} ---")
    
    # PIL 이미지를 다루기 위해 Image import (이미 상단에 있을 수 있지만, 명시적으로 확인)
    # from PIL import Image # 이미 파일 상단에 import 되어 있으므로 여기서는 주석 처리
    # json 모듈 import (이미 상단에 있을 수 있지만, 명시적으로 확인)
    # import json # 이미 파일 상단에 import 되어 있으므로 여기서는 주석 처리

    processed_crops = preprocess_answer_sheet(test_original_image_path, test_answer_key_json_path)

    if not processed_crops:
        print("Preprocessing returned no crops. Test did not generate any output.")
    else:
        print(f"\nPreprocessing finished. Number of cropped answer regions: {len(processed_crops)}")
        print("Details of processed crops (Key and Image Size):")
        for key, img_obj in processed_crops.items():
            # img_obj가 PIL Image 객체인지 확인 후 size 속성 접근
            if hasattr(img_obj, 'size'):
                print(f"  Key: {key}, Image Size: {img_obj.size}")
            else:
                print(f"  Key: {key}, Image Object Type: {type(img_obj)} (Size not available)")


    print("\n--- Test Script Finished ---")
