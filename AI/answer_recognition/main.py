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
from io import BytesIO
import base64
from paddleocr import PaddleOCR

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
    answer_key_data: Dict[str, Any],
) -> Dict[str, Image.Image]:
    final_ans_text_crop_dict: Dict[str, Image.Image] = {}
    if not Path(original_image_path).exists():
        print(f"Error: Missing original image: {original_image_path}")
        return {}
    
    if not answer_key_data:
        print(f"Error: Empty answer key data")
        return {}

    try:
        original_pil_image = Image.open(original_image_path).convert("RGB")
    except Exception as e:
        print(f"Error opening image file for preprocessing: {e}")
        return {}
        
    subject_name = Path(original_image_path).parent.name # 과목명 (상위 디렉토리명)
    subject_student_id_base = Path(original_image_path).stem
    
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
    # print(f"  [Debug Main] 생성된 question_info_dict (키 개수: {len(question_info_dict)}):")
    # json.dumps를 사용하여 보기 좋게 출력, 한글 깨짐 방지 ensure_ascii=False
    # 너무 길 경우 일부만 출력하거나, 파일로 저장하는 것을 고려할 수 있습니다.
    # 여기서는 전체를 출력합니다.
    # try:
    #     print(json.dumps(question_info_dict, indent=2, ensure_ascii=False))
    # except TypeError as e:
    #     # PIL Image 객체 등이 직접 포함되어 json.dumps가 실패하는 경우를 대비
    #     print(f"    question_info_dict를 JSON으로 변환 중 오류 (직접 출력 시도): {e}")
    #     print(question_info_dict) # 이 경우, 일반 print로 출력
    # --- question_info_dict 출력 디버그 코드 끝 ---


    if not question_info_dict: 
        print(f"  질문 정보 딕셔너리 생성 실패 {subject_student_id_base}. 질문 발견 및 답변 키 일치 확인 필요.")
        return {}


    # 여기가 문제!!!!!!!!! 텍스트 크롭이 너무 구림!!
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
        # line_cropped_ans_list: [{'image_obj': Image, 'y_top_in_area': int, 'y_bottom_in_area': int}]








    # 수평 크롭 결과 이미지 저장!!!!!!!!!!!!!!!!: plzzzzz_line_image 폴더에 저장됨
    # if not os.path.exists('/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_line_image'):
    #     os.makedirs('/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_line_image')
    # for idx, line_crop_data in enumerate(line_cropped_ans_list):
    #     line_image = line_crop_data['image_obj']
    #     line_y_top = line_crop_data['y_top_in_area']
    #     line_y_bottom = line_crop_data['y_bottom_in_area']
        
    #     # 파일명 생성
    #     line_image_filename = f"{subject_student_id_base}_line_{idx}_y{line_y_top}-{line_y_bottom}.png"
        
    #     # 이미지 저장
    #     line_image.save(os.path.join('/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_line_image', line_image_filename))









    # 이 루프는 line_cropped_ans_list에 있는 각 라인 조각에 대해 반복됩니다. 
    # line_idx는 현재 라인의 인덱스, line_crop_data는 현재 라인 이미지와 y정보를 담은 딕셔너리입니다.
    for line_idx, line_crop_data in enumerate(line_cropped_ans_list): # line_cropped_ans_list: [{'image_obj': Image, 'y_top_in_area': int, 'y_bottom_in_area': int}]
        line_ans_pil = line_crop_data['image_obj']

        line_y_top_in_ans_area = line_crop_data['y_top_in_area']
        current_line_id = f"{line_idx}" # 실제 current_line_id는 여기서 할당됨 (키 생성 등에 사용)

        # 라인 내 텍스트 컨투어(윤곽선) 검출
        text_contours_cv = preprocess_line_image_for_text_contours(line_ans_pil)
        # 텍스트 컨투어 병합 및 개별 텍스트 이미지 추출
        final_ans_text_crops_in_line = merge_contours_and_crop_text_pil(line_ans_pil, text_contours_cv) # horizontally_crop_image -> text_crop images








        # 텍스트 크롭 결과 이미지 저장!!!!!!!!!!!!!!!!: plzzzzz_text_crop_image 폴더에 저장됨
        # for idx, text_crop_data_in_line in enumerate(final_ans_text_crops_in_line):
            
        #     text_crop_image = text_crop_data_in_line['image_obj']
        #     line_dir_path = os.path.join('/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_text_crop_image', f"{line_idx}")
        #     if not os.path.exists(line_dir_path):
        #         os.makedirs(line_dir_path)
        #     text_crop_image.save(os.path.join('/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_text_crop_image',f"{line_idx}", f"{subject_student_id_base}_line_{line_idx}_text_crop_{idx}.png"))



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
            final_ans_text_crop_dict[final_key] = ans_text_crop_pil

    
    print(f"  전처리 완료: {subject_student_id_base}. 총 {len(final_ans_text_crop_dict)}개의 잘린 답변 텍스트 이미지 생성됨.") # DEBUG KOR
    print("final_ans_text_crop_dict:", final_ans_text_crop_dict)
    return final_ans_text_crop_dict






def recognize_answer_sheet_data(
    processed_ans_crops: Dict[str, Image.Image], # preprocess_answer_sheet 함수의 반환 값
    answer_key_data: Dict[str, Any],
    tail_question_counts: Dict[str, int]
) -> Dict[str, Any]:
    """
    전처리된 답안 텍스트 조각 이미지들로부터 숫자를 인식하여
    최종적으로 answer_json 및 failure_json을 생성합니다.

    Returns:
        Dict[str, Any]: answer_json과 failure_json을 포함하는 딕셔너리.
    """
    import re
    from collections import defaultdict
    
    # --- 0단계: 초기 유효성 검증 및 기본 정보 파싱 ---
    if not processed_ans_crops:
        return {
            "answer_json": {},
            "failure_json": {}
        }

    # 첫 번째 키 하나를 샘플로 추출하여 subject와 student_id 파싱
    sample_key = next(iter(processed_ans_crops))
    try:
        # 예시 키: test_answer_32174515_LL1_x60_qn1_ac0
        student_id_match = re.search(r"\d{8}", sample_key)
        if not student_id_match:
            raise ValueError("학번(8자리 숫자)을 key에서 찾을 수 없습니다.")
        
        student_id = student_id_match.group()
        subject_with_id = sample_key[:sample_key.find(student_id) + len(student_id)]
        subject = subject_with_id.rsplit("_", 1)[0]

    except Exception as e:
        return {
            "answer_json": {},
            "failure_json": {}
        }








    # --- 1단계: 이미지 그룹핑 및 좌표 파싱 ---
    from sklearn.cluster import KMeans
    import numpy as np

    
    grouped_answers_by_qn = {}

    for key, img in processed_ans_crops.items():
        # 1. 문제 번호 파싱 (qn)
        qn_match = re.search(r'_qn([a-zA-Z0-9\-]+)', key)
        qn = qn_match.group(1) if qn_match else "unknownQN"

        # 좌표 파싱
        x_match = re.search(r'_x(\d+)', key)
        y_match = re.search(r'_y(\d+)', key)
        x = int(x_match.group(1)) if x_match else -1
        y = int(y_match.group(1)) if y_match else -1

        entry = {
            "key": key,
            "img": img,
            "x": x,
            "y": y
        }
        
        # unknownQN인 경우 경고 메시지 출력하고 건너뛰기
        if qn == "unknownQN":
            continue
            
        # 2. 문제 단위 그룹핑
        if qn not in grouped_answers_by_qn:
            grouped_answers_by_qn[qn] = []

        grouped_answers_by_qn[qn].append(entry)

    # 3. qn - sub_qn 할당
    grouped_answers_by_qn_and_subqn = {}
    # tail_question_counts = extract_tail_question_counts(answer_key_data)

    # 3-1. 시험지 유형1: 꼬리문제가 없는 경우
    if all(value == 1 for value in tail_question_counts.values()):
        for qn, entries in grouped_answers_by_qn.items():
            # 꼬리문제가 없는 경우: qn만 사용하여 x 기준 정렬
            for idx, entry in enumerate(sorted(entries, key=lambda e: e["x"])):
                full_qn = qn  # sub_qn 없음

                if full_qn not in grouped_answers_by_qn_and_subqn:
                    grouped_answers_by_qn_and_subqn[full_qn] = []

                grouped_answers_by_qn_and_subqn[full_qn].append(entry)

    # 3-2. 시험지 유형2: 꼬리문제가 있고 qn에 포함되는 경우 - 신호와 시스템 시험지 유형
    elif any('-' in key for key in grouped_answers_by_qn.keys()):
        for qn, entries in grouped_answers_by_qn.items():
            # 꼬리문제가 없는 경우: qn만 사용하여 x 기준 정렬
            for idx, entry in enumerate(sorted(entries, key=lambda e: e["x"])):
                full_qn = qn  # sub_qn 없음

                if full_qn not in grouped_answers_by_qn_and_subqn:
                    grouped_answers_by_qn_and_subqn[full_qn] = []

                grouped_answers_by_qn_and_subqn[full_qn].append(entry)

    # 3-3. 시험지 유형3: 꼬리문제가 있고 qn에 포함되지 않는 경우 - 인공지능 시험지 유형
    else:
        for qn, entries in grouped_answers_by_qn.items():
            entries_sorted = sorted(entries, key=lambda e: e["y"])

            if qn in tail_question_counts and tail_question_counts[qn] > 1:
                # 어떤 주 문제의 꼬리문제가 여러 개인 경우: y 기준 KMeans 클러스터링 사용

                k = tail_question_counts[qn]
                y_values = np.array([e["y"] for e in entries_sorted]).reshape(-1, 1)

                try:
                    kmeans = KMeans(n_clusters=k, random_state=0, n_init="auto")
                    cluster_labels = kmeans.fit_predict(y_values)

                    # 중심 y값 기준으로 sub_qn 재정렬
                    cluster_centers = kmeans.cluster_centers_.flatten()
                    sorted_cluster_indices = np.argsort(cluster_centers)
                    cluster_to_subqn = {cluster_idx: sub_qn + 1 for sub_qn, cluster_idx in enumerate(sorted_cluster_indices)}

                except Exception as e:
                    cluster_labels = list(range(len(entries_sorted)))
                    cluster_to_subqn = {i: i + 1 for i in range(len(entries_sorted))}

                for idx, entry in enumerate(entries_sorted):
                    cluster_idx = cluster_labels[idx]
                    sub_qn = cluster_to_subqn[cluster_idx]
                    full_qn = f"{qn}-{sub_qn}"

                    if full_qn not in grouped_answers_by_qn_and_subqn:
                        grouped_answers_by_qn_and_subqn[full_qn] = []
                    grouped_answers_by_qn_and_subqn[full_qn].append(entry)

            else:
                for idx, entry in enumerate(sorted(entries_sorted, key=lambda e: e["x"])):
                    full_qn = qn
                    if full_qn not in grouped_answers_by_qn_and_subqn:
                        grouped_answers_by_qn_and_subqn[full_qn] = []
                    grouped_answers_by_qn_and_subqn[full_qn].append(entry)

    # 4. full_qn 기준으로 grouped_answers_by_qn_and_subqn 정렬
    def qn_sort_key(qn_str):
        if '-' in qn_str:
            major, minor = qn_str.split('-')
            return float(f"{int(major)}.{int(minor):02d}")
        else:
            return float(f"{int(qn_str)}.00")

    grouped_answers_by_qn_and_subqn = dict(
        sorted(grouped_answers_by_qn_and_subqn.items(), key=lambda x: qn_sort_key(x[0]))
    )

    # grouped_answers_by_qn_and_subqn 형식 확인하기
    debug_filename = os.path.join(os.getcwd(), "grouped_answers_by_qn_and_subqn_debug.txt")
    with open(debug_filename, 'w', encoding='utf-8') as debug_file:
        for full_qn, entries in grouped_answers_by_qn_and_subqn.items():
            debug_file.write(f"Question: {full_qn}\n")
            for entry in entries:
                debug_file.write(f"  Entry: {entry}\n")
            debug_file.write("\n")



    # --- 2단계: 개별 이미지에 대한 숫자 인식 수행 ---
    # 1. answer_key_data 기반 초기화
    answer_json_studentAnswers = {
        "student_id": student_id,
        "student_name": "", # 알 수 없음. 백엔드에서 추가해줘야함
        "subject": subject,
        "total_score": 0, # 채점 단계에서 추가해야한다.
        "answers": [
            {
                "question_number": entry["question_number"],
                "sub_question_number": entry["sub_question_number"],
                "student_answer": "",
                "answer_count": entry["answer_count"], 
                "confidence": 0, 
                "is_correct": False, # 채점 단계에서 추가해야한다.
                "score": 0, # 채점 단계에서 추가해야한다.
                "point": entry["point"]
            }
            for entry in answer_key_data.get("questions", [])
        ]
    }

    failure_json_images = []

    '''
    [grouped_answers_by_qn_and_subqn]

    Question: 1-1
    Entry: {'key': '신호및시스템-10_32201959_L1_x423_y897_qn1-1_ac1', 'img': <PIL.Image.Image image mode=RGB size=72x72 at 0x349C300E0>, 'x': 423, 'y': 897}

    Question: 2-1
    Entry: {'key': '신호및시스템-10_32201959_L2_x414_y1014_qn2-1_ac1', 'img': <PIL.Image.Image image mode=RGB size=85x85 at 0x349C33E60>, 'x': 414, 'y': 1014}

    Question: 2-2
    Entry: {'key': '신호및시스템-10_32201959_L3_x396_y1143_qn2-2_ac1', 'img': <PIL.Image.Image image mode=RGB size=74x74 at 0x349C324B0>, 'x': 396, 'y': 1143}

    Question: 2-3
    Entry: {'key': '신호및시스템-10_32201959_L4_x374_y1251_qn2-3_ac1', 'img': <PIL.Image.Image image mode=RGB size=79x79 at 0x349C32EA0>, 'x': 374, 'y': 1251}
    ...

    '''

    # 각 full_qn에 대해 처리
    total_digit_crops_count = 0
    for idx, (full_qn, entries) in enumerate(grouped_answers_by_qn_and_subqn.items()):
        # 한 문제에 대해 텍스트 크롭 이미지가 왼쪽부터 오른쪽으로 정렬되어 entries_sorted 리스트에 들어가있다.
        entries_sorted = sorted(entries, key=lambda e: e["x"])

        # 2. 한 문제에 대한 qn, sub_qn, ac 파싱(몇 번 문제인지, 답 개수는 몇 개인지 확인)
        if '-' in full_qn:
            qn, sub_qn = map(int, full_qn.split('-'))
        else:
            qn = int(full_qn)
            sub_qn = 0

        ac_match = re.search(r'_ac(\d+)', entries_sorted[0]['key'])
        ac = int(ac_match.group(1)) if ac_match else 1

        digit_crops = [] 
        # 우선 한 개의 텍스트 크롭 이미지에 대해 컨투어를 인식한다.
        # 컨투어별로 바운딩박스 크롭하여 single digit 이미지들을 만들어 digit_crops 리스트에 추가한다.

        # 3. 이미지로부터 숫자 컨투어 추출 및 중심 좌표 계산
        for entry_idx, entry in enumerate(entries_sorted):
            pil_img = entry['img'].convert('L')
            np_img = np.array(pil_img)
            _, thresh = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 먼저 모든 contour의 높이를 확인해서 최대 높이를 구함
            max_height = 0
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h >= 5 and w >= 5:  # 기본 크기 조건을 만족하는 것만 고려
                    max_height = max(max_height, h)
            
            # 최대 높이의 60% 임계값 계산
            height_threshold = max_height * 0.6

            entry_digit_count = 0
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h < 5 or w < 5:
                    continue
                # 높이가 최대 높이의 60% 미만이면 제외
                if h < height_threshold:
                    continue
                crop = pil_img.crop((x, y, x + w, y + h))
                xc, yc = x + w // 2, y + h // 2
                digit_crops.append((crop, (xc, yc)))
                entry_digit_count += 1

        total_digit_crops_count += len(digit_crops)

        if not digit_crops:
            continue

        # 4. 유클리드 거리 기반으로 ac-1개의 split 인덱스 결정
        ac_splits = ac - 1
        if ac_splits > 0:
            centers_sorted = sorted(digit_crops, key=lambda t: t[1][0])
            distances = [np.linalg.norm(np.array(centers_sorted[i+1][1]) - np.array(centers_sorted[i][1]))
                        for i in range(len(centers_sorted) - 1)]
            split_indices = np.argsort(distances)[-ac_splits:]
            split_indices = sorted(split_indices)
        else:
            split_indices = []

        # 5. split index 기준으로 숫자 그룹핑 - 이미지 대신 인식 결과를 그룹핑
        digits_grouped = []
        temp_group = []
        
        # MNIST 모델 파이프라인 가져오기
        pipe = mnist_recognition_pipeline
        
        # 각 digit crop을 먼저 인식하여 숫자로 변환
        recognized_digits = []
        digit_confidences = []
        for i, (img, coord) in enumerate(sorted(digit_crops, key=lambda t: t[1][0])):
            try:
                # 개별 digit 이미지 인식
                pred = pipe(img.convert('L'))
                if pred and len(pred) > 0:
                    predicted_digit = pred[0]['label']
                    confidence = pred[0].get('score', 0.0)
                    digit_confidences.append(confidence)
                    # 신뢰도가 낮으면 '?'로 표시
                    if confidence < 0.85:  # 개별 digit의 낮은 임계값
                        predicted_digit = '?'
                    recognized_digits.append(predicted_digit)
                else:
                    recognized_digits.append('?')
                    digit_confidences.append(0.0)
            except Exception as e:
                recognized_digits.append('?')
                digit_confidences.append(0.0)
        
        # 인식된 숫자들을 split_indices 기준으로 그룹핑
        for i, digit in enumerate(recognized_digits):
            temp_group.append(digit)
            if i in split_indices:
                digits_grouped.append(temp_group)
                temp_group = []
        if temp_group:
            digits_grouped.append(temp_group)

        # 6. 그룹별로 숫자 문자열 생성
        fail_flag = False
        result_string = ""
        confidence_threshold = 0.85  # 전체 신뢰도 임계값

        # digits_grouped의 예시
        # digits_grouped를 txt로 저장
        with open(os.path.join(os.getcwd(), "digits_grouped_output.txt"), "a") as f:
            for group in digits_grouped:
                # 사용자가 원하는 형태로 출력: group: ['숫자', '?', ...]
                print(f"group: {group}")
                # 각 그룹의 숫자들을 텍스트로 변환하여 저장
                group_text = ", ".join([str(digit) for digit in group])
                f.write(group_text + "\n")

            print("--------------------------------")

        # 그룹별로 숫자 문자열 생성
        for group_idx, group in enumerate(digits_grouped):
            # '?'가 포함된 그룹은 실패로 처리
            if '?' in group:
                fail_flag = True
                break
                
            # 그룹 내 숫자들을 연결하여 문자열 생성
            group_string = ''.join(group)
            result_string += group_string
        
        # 전체 신뢰도 계산 (평균)
        if digit_confidences and not fail_flag:
            avg_confidence = sum(digit_confidences) / len(digit_confidences)
        else:
            avg_confidence = 0.0

        # 7. 결과 저장: 실패 시 base64 이미지 저장, 성공 시 answer 기록
        if fail_flag or not result_string:
            # 원본 이미지들을 수평으로 연결
            width = sum([e['img'].width for e in entries_sorted])
            height = max([e['img'].height for e in entries_sorted])
            concat_img = Image.new("RGB", (width, height), color=(255, 255, 255))
            current_x = 0
            for e in entries_sorted:
                concat_img.paste(e['img'], (current_x, 0))
                current_x += e['img'].width
            
            try:
                buffered = BytesIO()
                concat_img.save(buffered, format="JPEG")
                img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                failure_reason = "신뢰도 부족" if fail_flag and result_string else "인식 불가"
                failure_entry = {
                    "student_id": student_id,
                    "file_name": "",
                    "base64_data": img_str,  # 전체 저장
                    "question_number": qn,
                    "sub_question_number": sub_qn
                    # "failure_reason": failure_reason  # 실패 이유 추가
                }
                
                failure_json_images.append(failure_entry)
                
            except Exception as e:
                pass
        else:            
            # answer_json에서 해당 문제 찾아서 답안 기록
            found_answer = False
            original_answer = ""
            for a in answer_json_studentAnswers["answers"]:
                if a["question_number"] == qn and a["sub_question_number"] == sub_qn:
                    original_answer = a["student_answer"]  # 기존 답안 백업
                    a["student_answer"] = result_string
                    a["confidence"] = avg_confidence
                    found_answer = True
                    break
            
            if not found_answer:
                pass


    # 최종 결과 리턴
    return {
        "answer_json": answer_json_studentAnswers,
        "failure_json": failure_json_images
    }

if __name__ == "__main__":
    # preprocess_answer_sheet 함수 테스트

    # 인공지능 시험지
    # test_original_image_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer/32174515.jpg'
    # test_answer_key_json_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer.json'

    # 신호와 시스템 시험지(최종 테스트용) - 신호및시스템-14로 변경
    test_original_image_path = '/home/jdh251425/2025_DKU_Capstone/AI/plzzzzz_home/신호및시스템-9_32202698.jpg'
    test_answer_key_json_path = '/home/jdh251425/2025_DKU_Capstone/AI/test_data_signals/test_answer.json'

    # JSON 파일을 딕셔너리로 로드
    with open(test_answer_key_json_path, 'r', encoding='utf-8') as f:
        answer_key_data = json.load(f)

    final_ans_text_crop_dict = preprocess_answer_sheet(test_original_image_path, answer_key_data)
    
    # 인식 단계 추가 - group별 결과를 보기 위해
    if final_ans_text_crop_dict:
        # tail_question_counts 계산
        tail_question_counts = {}
        for q_entry in answer_key_data.get('questions', []):
            qn = q_entry.get('question_number')
            if qn:
                if qn not in tail_question_counts:
                    tail_question_counts[qn] = 0
                tail_question_counts[qn] += 1
        
        # 인식 수행
        recognition_results = recognize_answer_sheet_data(final_ans_text_crop_dict, answer_key_data, tail_question_counts)
        print(f"\n인식 완료: {len(recognition_results.get('answer_json', {}).get('answers', []))}개 답변 처리")
