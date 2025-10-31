from typing import Dict, List, Any, Tuple
import re
# import os # 디버그 이미지 저장용 - 제거
# from pathlib import Path # 디버그 이미지 저장용 - 제거

# data_structures는 상위 디렉토리 또는 answer_recognition 패키지 레벨에서 가져와야 함
# 현재 key_utils.py는 answer_recognition/utils/ 안에 위치
from ..data_structures import DetectedArea
# 이미지 처리 함수들 import
from ..preprocessing.image_utils import (
    preprocess_line_image_for_text_contours, 
    merge_contours_and_crop_text_pil,
    enhance_and_find_contours_for_lines,
    crop_between_lines
)
# 숫자 인식 함수는 이제 직접 사용하지 않음


def create_question_info_dict(
    qn_detected_areas: List[DetectedArea],
    answer_key_data: Dict[str, Any]
) -> Dict[str, List[int]]:
    # Step 1: answer_key.json에서 문제 목록 준비 (A: 하위 포함, B: 주 문제만)
    question_list_from_key_a = [] 
    question_list_from_key_b_set = set()
    for q_entry in answer_key_data.get('questions', []):
        qn_str = str(q_entry.get('question_number', ''))
        sub_qn_val = q_entry.get('sub_question_number', 0)
        sub_qn_str = str(sub_qn_val) if sub_qn_val and str(sub_qn_val) != "0" else ""
        if qn_str:
            full_qn_str = f"{qn_str}-{sub_qn_str}" if sub_qn_str else qn_str
            question_list_from_key_a.append(full_qn_str)
            question_list_from_key_b_set.add(qn_str)

    def qn_sort_key(q_str_local: str):
        parts = q_str_local.split('-')
        key_parts = []
        for part in parts:
            if part.isdigit(): key_parts.append(int(part))
            else: 
                match = re.match(r"(\d+)([a-zA-Z]*)", part)
                if match: num_part, str_part_val = match.groups(); key_parts.append(int(num_part)); 
                if str_part_val: key_parts.append(str_part_val)
                else: key_parts.append(part)
        return tuple(key_parts)

    sorted_question_list_a = sorted(list(set(question_list_from_key_a)), key=qn_sort_key)
    sorted_question_list_b = sorted(list(question_list_from_key_b_set), key=qn_sort_key)
    len_a = len(sorted_question_list_a)
    len_b = len(sorted_question_list_b)

    if not qn_detected_areas:
        print("Error (create_question_info_dict): No QN areas detected by YOLO."); return {}

    # Step 2: QN 영역 내 텍스트 객체 검출 및 y좌표 추출
    # 이제 항상 하나의 QN 영역만 존재한다고 가정합니다.
    main_qn_area = qn_detected_areas[0]
    qn_area_pil = main_qn_area['image_obj'] # qn_half_cropped 이미지에 해당
    # qn_area_orig_y_offset = main_qn_area['bbox'][1] # 원본 답안지 기준 y 오프셋. 이제 사용하지 않음.

    # 수정된 로직: 수평선을 기준으로 QN 영역을 자르고, 그 개수를 사용합니다.
    line_contours_in_qn = enhance_and_find_contours_for_lines(qn_area_pil)
    # crop_between_lines는 [{'image_obj': Image, 'y_top_in_area': int, 'y_bottom_in_area': int}, ...] 형태의 리스트 반환
    line_cropped_list_in_qn = crop_between_lines(qn_area_pil, line_contours_in_qn)

    detected_objects_y_coords: List[Tuple[int, int]] = []
    for line_info in line_cropped_list_in_qn:
        # qn_half_cropped 이미지 (즉, qn_area_pil) 기준의 y좌표를 사용합니다.
        y_top_in_qn_half_cropped = line_info['y_top_in_area']
        y_bottom_in_qn_half_cropped = line_info['y_bottom_in_area']
        detected_objects_y_coords.append((y_top_in_qn_half_cropped, y_bottom_in_qn_half_cropped))
    
    # crop_between_lines에서 이미 y_top 기준으로 정렬된 결과를 반환할 수 있지만,
    # 안전을 위해 여기서 다시 명시적으로 정렬합니다.
    detected_objects_y_coords.sort(key=lambda y_pair: y_pair[0])
    num_detected_text_objects = len(detected_objects_y_coords) # 또는 len(line_cropped_list_in_qn)

    # print(f"Debug: Num detected text objects in QN: {num_detected_text_objects}")
    # print(f"Debug: Detected objects y_coords (first 5): {detected_objects_y_coords[:5]}")
    # print(f"Debug: len_a={len_a}, len_b={len_b}")

    y_coordinates_dict: Dict[str, List[int]] = {}
    target_question_list = []
    y_coords_to_use = detected_objects_y_coords
    match_type = ""

    # Step 3: 매칭 로직
    is_case_a_equals_b = (len_a == len_b)

    if is_case_a_equals_b: # 하위 문제 없음 (a==b)
        if num_detected_text_objects == len_b: # 개수 정확히 일치 (헤더 X)
            target_question_list = sorted_question_list_b
            match_type = f"Exact match with B ({len_b}) - No header assumed."
        elif num_detected_text_objects == len_b + 1: # 헤더 포함 가능성 (1개 더 많음)
            target_question_list = sorted_question_list_b
            y_coords_to_use = detected_objects_y_coords[1:] # 첫번째 객체(헤더) 제외
            match_type = f"Match with B ({len_b}) after removing 1 header. Detected: {num_detected_text_objects}"
        elif num_detected_text_objects == len_b - 1: # 1개 부족
            target_question_list = sorted_question_list_b
            # y_coords_to_use는 그대로 두고, 짧은 쪽(num_detected_text_objects) 만큼만 매칭
            match_type = f"Potential mismatch: Detected ({num_detected_text_objects}) is 1 less than B ({len_b}). Matching shorter length."
        else: # 그 외 불일치
            match_type = f"Mismatch: Detected ({num_detected_text_objects}) vs B ({len_b})."
            
    else: # 하위 문제 있음 (a!=b)
        # 1. '개수'가 a 또는 b와 일치 (헤더 X)
        if num_detected_text_objects == len_a:
            target_question_list = sorted_question_list_a
            match_type = f"Exact match with A ({len_a}) - No header assumed."
        elif num_detected_text_objects == len_b:
            target_question_list = sorted_question_list_b
            match_type = f"Exact match with B ({len_b}) - No header assumed."
        # 2. '개수'가 a+-1 또는 b+-1 (헤더 가능성)
        elif num_detected_text_objects == len_a + 1:
            target_question_list = sorted_question_list_a
            y_coords_to_use = detected_objects_y_coords[1:]
            match_type = f"Match with A ({len_a}) after removing 1 header. Detected: {num_detected_text_objects}"
        elif num_detected_text_objects == len_b + 1:
            target_question_list = sorted_question_list_b
            y_coords_to_use = detected_objects_y_coords[1:]
            match_type = f"Match with B ({len_b}) after removing 1 header. Detected: {num_detected_text_objects}"
        elif num_detected_text_objects == len_a - 1:
            target_question_list = sorted_question_list_a
            match_type = f"Potential mismatch: Detected ({num_detected_text_objects}) is 1 less than A ({len_a}). Matching shorter length."
        elif num_detected_text_objects == len_b - 1:
            target_question_list = sorted_question_list_b
            match_type = f"Potential mismatch: Detected ({num_detected_text_objects}) is 1 less than B ({len_b}). Matching shorter length."
        else:
             match_type = f"Mismatch: Detected ({num_detected_text_objects}) vs A ({len_a}) or B ({len_b})."

    # print(f"Debug: Match type: {match_type}")
    # print(f"Debug: Target question list (len={len(target_question_list)}): {target_question_list[:5]}...")
    # print(f"Debug: Y-coords to use (len={len(y_coords_to_use)}): {y_coords_to_use[:5]}...")

    if target_question_list and y_coords_to_use:
        # 매칭 시 짧은 쪽 길이를 기준으로 함
        min_len = min(len(target_question_list), len(y_coords_to_use))
        if min_len > 0 :
            # print(f"Info (create_question_info_dict): {match_type} Attempting to map {min_len} QN items.")
            for i in range(min_len):
                y_coordinates_dict[target_question_list[i]] = [y_coords_to_use[i][0], y_coords_to_use[i][1]]
        else:
             print(f"Warning (create_question_info_dict): {match_type} But min_len for mapping is 0. No QN info generated.")
    
    if not y_coordinates_dict:
        print(f"Error (create_question_info_dict): Failed to create question_info_dict. Match type: {match_type}")
        print(f"  Num detected text objects in QN: {num_detected_text_objects}")
        print(f"  Num questions in key A (sub-QN): {len_a}, B (main QN): {len_b}")
        print(f"  DEBUG: Detected objects y_coords (first 5): {detected_objects_y_coords[:5]}")
        return {}
        
    return y_coordinates_dict


def generate_final_key_for_ans_crop(
    subject_student_id_base: str, # "과목명_학번"
    ans_text_crop_full_info: Dict[str, Any], 
    question_info_dict: Dict[str, List[int]], 
    answer_key_data: Dict[str, Any]
) -> str:
    # 디버그: 현재 처리중인 텍스트 조각 정보
    line_id_for_debug = ans_text_crop_full_info.get('line_id_in_ans_area', 'unknownLine')
    x_coord_for_debug = ans_text_crop_full_info.get('x_in_line', -1)
    # print(f"[Debug KeyGen] 처리 시작: ID={subject_student_id_base}, Line={line_id_for_debug}, X={x_coord_for_debug}")

    y_in_line = ans_text_crop_full_info['y_in_line_relative_to_line_crop_top']
    line_y_top = ans_text_crop_full_info['line_y_top_relative_to_ans_area']
    ans_area_y_offset = ans_text_crop_full_info['ans_area_y_offset_orig']
    text_crop_height = ans_text_crop_full_info['image_obj'].height
    abs_y_top_of_text_crop = ans_area_y_offset + line_y_top + y_in_line
    abs_y_center_of_text_crop = line_y_top + (text_crop_height // 2)

    # print(f"  [Debug KeyGen] 계산된 텍스트 y 중심: {abs_y_center_of_text_crop}")

    matching_qn_str = "unknownQN"
    # print(f"  [Debug KeyGen] 문제번호 매칭 시도...")
    for qn_key, y_range_orig in question_info_dict.items():
        # print(f"    - 확인 중: qn_key='{qn_key}', y_range={y_range_orig}. (텍스트 y 중심: {abs_y_center_of_text_crop})")
        if y_range_orig[0] <= abs_y_center_of_text_crop <= y_range_orig[1]:
            matching_qn_str = qn_key
            # print(f"      ==> 매칭 성공: '{matching_qn_str}'")
            break
    
    if matching_qn_str == "unknownQN":
        # print(f"  [Debug KeyGen] 최종 문제번호 매칭 실패: matching_qn_str = 'unknownQN'")
        # --- "unknownQN"으로 매칭된 경우 ans_text_crop_pil 이미지 저장 디버그 코드 시작 ---
        # try:
        #     image_to_save = ans_text_crop_full_info['image_obj']
        #     debug_image_dir = Path("debug_unknown_qn_images")
        #     os.makedirs(debug_image_dir, exist_ok=True)
        #     
        #     # 파일명에 특수문자나 공백이 없도록 처리 고려 (여기서는 간단히 처리)
        #     safe_subject_id_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', subject_student_id_base)
        #     safe_line_id = re.sub(r'[^a-zA-Z0-9_\-]', '_', line_id_for_debug)
        #
        #     filename = f"{safe_subject_id_base}_{safe_line_id}_x{x_coord_for_debug}_yCenter{abs_y_center_of_text_crop}.png"
        #     save_path = debug_image_dir / filename
        #     image_to_save.save(save_path)
        #     print(f"  [Debug KeyGen] 'unknownQN' 이미지 저장됨: {save_path}")
        # except Exception as e:
        #     print(f"  [Debug KeyGen] 'unknownQN' 이미지 저장 중 오류: {e}")
        # --- "unknownQN"으로 매칭된 경우 ans_text_crop_pil 이미지 저장 디버그 코드 끝 ---
        pass # print 문과 이미지 저장 코드가 제거되었으므로, 필요한 경우 pass 추가

    answer_count_for_qn = 0
    for q_entry in answer_key_data.get('questions', []):
        qn_str_key = str(q_entry.get('question_number'))
        sub_qn_val = q_entry.get('sub_question_number', 0)
        sub_qn_str_key = str(sub_qn_val) if sub_qn_val and str(sub_qn_val) != "0" else ""
        current_key_in_answer_data = f"{qn_str_key}-{sub_qn_str_key}" if sub_qn_str_key else qn_str_key
        if current_key_in_answer_data == matching_qn_str:
            answer_count_for_qn = q_entry.get('answer_count', 0)
            break

            
    x_in_line_coord = ans_text_crop_full_info['x_in_line']
    line_id_in_ans_area = ans_text_crop_full_info.get('line_id_in_ans_area','lineX')

    # ans_area_id 부분을 키에서 제거
    key_base = f"{subject_student_id_base}_L{line_id_in_ans_area}_x{x_in_line_coord}_y{abs_y_top_of_text_crop}_qn{matching_qn_str}_ac{answer_count_for_qn}"
    
    return key_base.replace(" ", "") 