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

        line_y_top_in_ans_area = line_crop_data['y_top_in_area']
        current_line_id = f"{line_idx}" # 실제 current_line_id는 여기서 할당됨 (키 생성 등에 사용)

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
            final_ans_text_crop_dict[final_key] = ans_text_crop_pil

    
    print(f"  전처리 완료: {subject_student_id_base}. 총 {len(final_ans_text_crop_dict)}개의 잘린 답변 텍스트 이미지 생성됨.") # DEBUG KOR
    return final_ans_text_crop_dict






def recognize_answer_sheet_data(
    processed_ans_crops: Dict[str, Image.Image], # preprocess_answer_sheet 함수의 반환 값
    answer_key_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    전처리된 답안 텍스트 조각 이미지들로부터 숫자를 인식하여
    최종적으로 answer_json 및 failure_json을 생성합니다.

    Returns:
        Dict[str, Any]: answer_json과 failure_json을 포함하는 딕셔너리.
    """
    import re # Moved here
    from collections import defaultdict # Moved here
    
    # --- 0단계: 초기 유효성 검증 및 기본 정보 파싱 ---
    # 입력으로 받은 processed_ans_crops가 비어 있는 경우, 에러 메시지를 출력하고 빈 결과를 반환 (early return)
    # processed_ans_crops의 첫 번째 key를 샘플로 사용하여 아래 정보를 파싱:
        # 학번(student_id): key 내 8자리 숫자를 정규표현식으로 추출
        # 과목명(subject): key 내에서 학번 앞까지의 문자열 중 마지막 '_'를 기준으로 학번 제외
    # 이후 단계에서 사용할 결과 저장용 딕셔너리 answer_result / failure_result 초기화

    if not processed_ans_crops:
        print("[Error] 입력된 processed_ans_crops가 비어 있습니다.")
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

        print(f"[Init] 파싱된 subject: {subject}, student_id: {student_id}")
    except Exception as e:
        print(f"[Error] Key 파싱 실패 - 예외: {e}")
        return {
            "answer_json": {},
            "failure_json": {}
        }

    # 결과 저장용 딕셔너리 초기화
    answer_result: Dict[str, Dict[str, Any]] = {}
    failure_result: Dict[str, List[Dict[str, Any]]] = {}

    # --- 0단계 확인을 위한 임시 반환 ---
    # return {
    #     "parsed_subject": subject,
    #     "parsed_student_id": student_id,
    #     "initial_answer_result": answer_result,
    #     "initial_failure_result": failure_result,
    #     "message": "0단계 (초기화 및 파싱) 테스트 완료"
    # }









    # --- 1단계: 이미지 그룹핑 및 좌표 파싱 ---
    # • processed_ans_crops의 key를 순회하며 question number(qn)를 추출
    # • key 내부에서 x, y 좌표도 정규표현식으로 추출
    # • qn 값이 없을 경우 unknownQN으로 처리
    # • 각 qn에 대해 리스트 생성: { key, img, x, y } 딕셔너리 추가
    # • 각 qn 리스트 내 객체들을 y 오름차순 → x 오름차순으로 정렬
    import re
    from collections import defaultdict
    from sklearn.cluster import KMeans
    import numpy as np

    def extract_tail_question_counts(answer_key_data: dict) -> dict:
        """
        answer_key_data로부터 각 문제(qn)의 꼬리문제 개수(sub_question_number의 개수)를 계산합니다.

        Returns:
            tail_question_counts: Dict[str, int]
                예: {"1": 28, "2": 1, "3": 1, ...}
        """
        tail_question_counts = defaultdict(int)

        for q in answer_key_data.get("questions", []):
            qn = str(q["question_number"])
            tail_question_counts[qn] += 1

        return dict(tail_question_counts)
    
    

    # --- 1단계: 문제 번호(qn) 기준으로 그룹핑 및 좌표 정렬 ---
    # • processed_ans_crops의 각 key에서 문제 번호(qn), x, y 좌표를 파싱
    # • 각 qn별로 이미지들을 모아서 grouped_answers_by_qn에 저장
    # • 이때 (x, y) 좌표 정보를 함께 포함시켜 추후 정렬/클러스터링에 사용
    # • tail_question_counts를 기반으로 y 기준 KMeans 클러스터링이 필요한 문제를 식별함


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
            print(f"[Warning] Key '{key}'에서 유효한 문제 번호(qn)를 찾을 수 없습니다. 건너뜁니다.")
            continue
            
        # 2. 문제 단위 그룹핑
        if qn not in grouped_answers_by_qn:
            grouped_answers_by_qn[qn] = []

        grouped_answers_by_qn[qn].append(entry)

    # 3. qn - sub_qn 할당
    # 이제 각 qn에 대해 y 정렬 또는 KMeans 클러스터링을 적용해 sub_qn 할당
    grouped_answers_by_qn_and_subqn = {}
    tail_question_counts = extract_tail_question_counts(answer_key_data)
    '''
    tail_question_counts 예시:
    {
        "1": 28,
        "2": 1,
        "3": 1,
        "4": 1,
        "5": 1,
        ...
    }
    '''

    # 3-1. 시험지 유형1: 꼬리문제가 없는 경우
        # x 기준 정렬만 수행한다.
        # 왜냐하면 각 qn에는 꼬리문제가 없으므로, y 기준 정렬은 불필요하기 때문이다.
    if all(value == 1 for value in tail_question_counts.values()):
        for qn, entries in grouped_answers_by_qn.items():
            # 꼬리문제가 없는 경우: qn만 사용하여 x 기준 정렬
            for idx, entry in enumerate(sorted(entries, key=lambda e: e["x"])):
                full_qn = qn  # sub_qn 없음

                if full_qn not in grouped_answers_by_qn_and_subqn:
                    grouped_answers_by_qn_and_subqn[full_qn] = []

                grouped_answers_by_qn_and_subqn[full_qn].append(entry)


    # 3-2. 시험지 유형2: 꼬리문제가 있고 qn에 포함되는 경우 - 신호와 시스템 시험지 유형
        # 신호와 시스템 시험지의 경우 꼬리문제가 있고 qn에 포함된다.
        # 이런 경우 '시험지 유형1'과 동일하게 처리한다.
        # 참고로 '2(a)', '7(b)'와 같은 꼬리문제 형식이어도 qn은 항상 '2-1', '7-2'과 같은 형식으로 처리된다.(이는 preprocess_answer_sheet 함수와 답지.json에서 확인할 수 있다.)
    elif any('-' in key for key in grouped_answers_by_qn.keys()):
        for qn, entries in grouped_answers_by_qn.items():
            # 꼬리문제가 없는 경우: qn만 사용하여 x 기준 정렬
            for idx, entry in enumerate(sorted(entries, key=lambda e: e["x"])):
                full_qn = qn  # sub_qn 없음

                if full_qn not in grouped_answers_by_qn_and_subqn:
                    grouped_answers_by_qn_and_subqn[full_qn] = []

                grouped_answers_by_qn_and_subqn[full_qn].append(entry)


    # 3-3. 시험지 유형3: 꼬리문제가 있고 qn에 포함되지 않는 경우 - 인공지능 시험지 유형
        # 인공지능 시험지의 1번 문제의 경우 꼬리문제가 있고 qn_yolo_area(yolo 검출 기준)에 꼬리문제가 포함되지 않는다.
        # 이런 경우 꼬리문제가 있는 문제에 대해 텍스트 크롭 이미지들을 y 기준 정렬한다.
        # 그 후 꼬리문제 개수를 기준으로 KMeans 클러스터링을 수행한다.
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
                    print(f"[Error] qn {qn} KMeans 실패: {e}")
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
        # full_qn이 '1-2'와 같이 꼬리문제를 포함하는 경우를 고려해 정렬되도록 key를 float 값으로 변환
        # 예: '1-2' → 1.02, '2' → 2.00으로 변환하여 번호 순 정렬을 자연스럽게 수행
    def qn_sort_key(qn_str):
        if '-' in qn_str:
            major, minor = qn_str.split('-')
            return float(f"{int(major)}.{int(minor):02d}")
        else:
            return float(f"{int(qn_str)}.00")

    grouped_answers_by_qn_and_subqn = dict(
        sorted(grouped_answers_by_qn_and_subqn.items(), key=lambda x: qn_sort_key(x[0]))
    )

    # --- 텍스트 크롭 이미지 저장 (디버그) ---
    # 디렉토리 구조: {과목명}/{학번}/{full_qn}/{img}
    debug_output_dir = Path("debug_text_crops")
    subject_dir = debug_output_dir / subject
    student_dir = subject_dir / student_id
    
    try:
        student_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Debug] 디버그 이미지 저장 디렉토리 생성: {student_dir}")
        
        total_saved = 0
        for full_qn, entries in grouped_answers_by_qn_and_subqn.items():
            qn_dir = student_dir / full_qn
            qn_dir.mkdir(exist_ok=True)
            
            for idx, entry in enumerate(entries):
                img_obj = entry["img"]
                img_filename = f"{entry['key']}.png"
                img_path = qn_dir / img_filename
                
                if hasattr(img_obj, 'save'):
                    img_obj.save(str(img_path))
                    total_saved += 1
                else:
                    print(f"[Warning] Image object at {full_qn}[{idx}] is not a valid PIL Image")
        
        print(f"[Debug] 총 {total_saved}개의 텍스트 크롭 이미지가 {student_dir}에 저장되었습니다.")
        
    except Exception as e:
        print(f"[Error] 디버그 이미지 저장 중 오류 발생: {e}")




    # --- 1단계 확인을 위한 임시 반환 ---
    # grouped_answers_by_qn_and_subqn을 직렬화합니다.
    # 각 딕셔너리 내부의 'img' PIL Image 객체를 크기 정보로 대체합니다.
    # grouped_answers_serializable = {}
    # for full_qn, entries in grouped_answers_by_qn_and_subqn.items():
    #     serializable_entries = []
    #     for entry in entries:
    #         serializable_entry = entry.copy() # 원본 entry 수정을 피하기 위해 복사
    #         img_obj = serializable_entry.pop("img") # img 객체를 꺼내고 entry에서 제거
    #         serializable_entry["img_size"] = img_obj.size if hasattr(img_obj, 'size') else 'N/A'
    #         serializable_entries.append(serializable_entry)
    #     grouped_answers_serializable[full_qn] = serializable_entries
    
    # return {
    #     "parsed_subject": subject,
    #     "parsed_student_id": student_id,
    #     "grouped_answers_by_qn_and_subqn": grouped_answers_serializable, # 직렬화된 새 변수 사용 및 키 변경
    #     "message": "1단계 (이미지 그룹핑 및 sub_qn 할당) 테스트 완료" # 메시지 업데이트
    # }











    # --- 2단계: 개별 이미지에 대한 숫자 인식 수행 ---
    # • 이미지 내 숫자 컨투어 검출
    # • 컨투어 기반으로 숫자 박스 추출
    # • 모델을 통해 각 숫자 박스에 대해 숫자 인식 수행
    # • 인식된 숫자를 조합하여 최종 답안 문자열 생성

    print("\n--- 2단계: 개별 이미지에 대한 숫자 인식 수행 시작 ---")

    # 1. answer_key_data 기반 초기화
    print("1. answer_key_data 기반 초기화 중...")
    answer_json_studentAnswers = {
        "student_id": student_id,
        "answers": [
            {
                "question_number": entry["question_number"],
                "sub_question_number": entry["sub_question_number"],
                "student_answer": ""
            }
            for entry in answer_key_data.get("questions", [])
        ]
    }
    
    print(f"   초기화된 answer_json_studentAnswers (답안 개수: {len(answer_json_studentAnswers['answers'])}개):")
    for i, answer in enumerate(answer_json_studentAnswers['answers'][:5]):  # 처음 5개만 출력
        print(f"     [{i}] Q{answer['question_number']}-{answer['sub_question_number']}: '{answer['student_answer']}'")
    if len(answer_json_studentAnswers['answers']) > 5:
        print(f"     ... (총 {len(answer_json_studentAnswers['answers'])}개)")

    failure_json_images = []
    print(f"   failure_json_images 초기화 완료\n")

    # 각 full_qn에 대해 처리
    total_digit_crops_count = 0
    for idx, (full_qn, entries) in enumerate(grouped_answers_by_qn_and_subqn.items()):
        print(f"--- 처리 중: {full_qn} (이미지 {len(entries)}개) ---")
        entries_sorted = sorted(entries, key=lambda e: e["x"])

        # 2. qn, sub_qn 파싱
        if '-' in full_qn:
            qn, sub_qn = map(int, full_qn.split('-'))
        else:
            qn = int(full_qn)
            sub_qn = 1

        ac_match = re.search(r'_ac(\d+)', entries_sorted[0]['key'])
        ac = int(ac_match.group(1)) if ac_match else 1

        print(f"2. 파싱 결과: qn={qn}, sub_qn={sub_qn}, ac={ac}")
        print(f"   정렬된 이미지들의 x좌표: {[e['x'] for e in entries_sorted]}")

        digit_crops = []

        # 3. 이미지로부터 숫자 컨투어 추출 및 중심 좌표 계산
        print("3. 숫자 컨투어 추출 및 중심 좌표 계산 중...")
        for entry_idx, entry in enumerate(entries_sorted):
            pil_img = entry['img'].convert('L')
            np_img = np.array(pil_img)
            _, thresh = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            entry_digit_count = 0
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                if h < 5 or w < 5:
                    continue
                crop = pil_img.crop((x, y, x + w, y + h))
                xc, yc = x + w // 2, y + h // 2
                digit_crops.append((crop, (xc, yc)))
                entry_digit_count += 1

            print(f"   이미지 [{entry_idx}] (key: {entry['key'][:50]}...): {entry_digit_count}개 숫자 컨투어 발견")

        print(f"   {full_qn} 총 숫자 컨투어: {len(digit_crops)}개")
        total_digit_crops_count += len(digit_crops)
        
        if digit_crops:
            print(f"   중심 좌표 샘플 (처음 3개): {[coord for _, coord in digit_crops[:3]]}")
        else:
            print("   ⚠️  숫자 컨투어가 발견되지 않았습니다!")

        if not digit_crops:
            continue

        # 나머지 부분들은 주석처리
        '''
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

        # 5. split index 기준으로 숫자 그룹핑
        digits_grouped = []
        temp_group = []
        for i, (img, _) in enumerate(sorted(digit_crops, key=lambda t: t[1][0])):
            temp_group.append(img)
            if i in split_indices:
                digits_grouped.append(temp_group)
                temp_group = []
        if temp_group:
            digits_grouped.append(temp_group)
        '''

        # 4. 유클리드 거리 기반으로 ac-1개의 split 인덱스 결정
        print("4. 유클리드 거리 기반 split 인덱스 결정 중...")
        ac_splits = ac - 1
        if ac_splits > 0:
            centers_sorted = sorted(digit_crops, key=lambda t: t[1][0])
            distances = [np.linalg.norm(np.array(centers_sorted[i+1][1]) - np.array(centers_sorted[i][1]))
                        for i in range(len(centers_sorted) - 1)]
            split_indices = np.argsort(distances)[-ac_splits:]
            split_indices = sorted(split_indices)
            print(f"   ac={ac}, ac_splits={ac_splits}")
            print(f"   중심 좌표 정렬된 순서: {[coord for _, coord in centers_sorted]}")
            print(f"   인접 거리들: {distances}")
            print(f"   split_indices: {split_indices}")
        else:
            split_indices = []
            print(f"   ac={ac}, ac_splits={ac_splits} → split 불필요")

        # 5. split index 기준으로 숫자 그룹핑
        print("5. split index 기준 숫자 그룹핑 중...")
        digits_grouped = []
        temp_group = []
        for i, (img, coord) in enumerate(sorted(digit_crops, key=lambda t: t[1][0])):
            temp_group.append(img)
            print(f"   [{i}] 좌표 {coord} → temp_group에 추가 (현재 그룹 크기: {len(temp_group)})")
            if i in split_indices:
                digits_grouped.append(temp_group)
                print(f"   ✂️  split_index {i}에서 분할! → 그룹 {len(digits_grouped)} 생성 (크기: {len(temp_group)})")
                temp_group = []
        if temp_group:
            digits_grouped.append(temp_group)
            print(f"   🔚 마지막 그룹 추가 → 그룹 {len(digits_grouped)} 생성 (크기: {len(temp_group)})")
        
        print(f"   최종 그룹핑 결과: {len(digits_grouped)}개 그룹")
        for group_idx, group in enumerate(digits_grouped):
            print(f"     그룹 [{group_idx}]: {len(group)}개 숫자")

        # 6. 모델을 통한 숫자 인식 및 문자열 생성
        print("6. 모델을 통한 숫자 인식 및 문자열 생성 중...")
        fail_flag = False
        result_string = ""
        confidence_threshold = 0.85  # 신뢰도 임계값 설정
        
        # MNIST 모델 파이프라인 가져오기
        pipe = mnist_recognition_pipeline
        
        print(f"   digits_grouped: {len(digits_grouped)}개 그룹 (신뢰도 임계값: {confidence_threshold})")
        for group_idx, group in enumerate(digits_grouped):
            print(f"   그룹 [{group_idx}] 처리 중: {len(group)}개 숫자")
            
            if not pipe:
                print(f"     ❌ MNIST 모델이 없습니다!")
                fail_flag = True
                break
                
            # 그룹 내 이미지들을 수평으로 연결
            width = sum([img.width for img in group])
            height = max([img.height for img in group])
            new_img = Image.new("L", (width, height), color=255)
            current_x = 0
            for img_idx, img in enumerate(group):
                new_img.paste(img, (current_x, 0))
                print(f"     숫자 [{img_idx}] 붙여넣기: x={current_x}, 크기={img.size}")
                current_x += img.width
            
            print(f"     연결된 이미지 크기: {new_img.size}")
            
            try:
                pred = pipe(new_img)
                if not pred:
                    print(f"     ❌ 모델 예측 결과가 없습니다!")
                    fail_flag = True
                    break
                
                predicted_label = pred[0]['label']
                confidence = pred[0].get('score', 0.0)  # 기본값을 0.0으로 설정
                
                # 신뢰도 체크
                if confidence < confidence_threshold:
                    print(f"     ❌ 신뢰도 부족: '{predicted_label}' (신뢰도: {confidence:.4f} < {confidence_threshold})")
                    fail_flag = True
                    break
                
                print(f"     ✅ 예측 결과: '{predicted_label}' (신뢰도: {confidence:.4f})")
                result_string += predicted_label
                
            except Exception as e:
                print(f"     ❌ 모델 예측 중 오류: {e}")
                fail_flag = True
                break

        print(f"   최종 결과 문자열: '{result_string}' (실패: {fail_flag})")

        # 7. 결과 저장: 실패 시 base64 이미지 저장, 성공 시 answer 기록
        print("7. 결과 저장 중...")
        if fail_flag or not result_string:
            print("   실패 케이스 → failure_json에 base64 이미지 저장")
            
            # 원본 이미지들을 수평으로 연결
            width = sum([e['img'].width for e in entries_sorted])
            height = max([e['img'].height for e in entries_sorted])
            concat_img = Image.new("RGB", (width, height), color=(255, 255, 255))
            current_x = 0
            for e in entries_sorted:
                concat_img.paste(e['img'], (current_x, 0))
                current_x += e['img'].width

            print(f"     연결된 실패 이미지 크기: {concat_img.size}")
            
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
                print(f"     ✅ failure_json에 추가됨: Q{qn}-{sub_qn} (이유: {failure_reason})")
                
            except Exception as e:
                print(f"     ❌ base64 변환 중 오류: {e}")
        else:
            print(f"   성공 케이스 → answer_json에 답안 '{result_string}' 저장")
            
            # answer_json에서 해당 문제 찾아서 답안 기록
            found_answer = False
            original_answer = ""
            for a in answer_json_studentAnswers["answers"]:
                if a["question_number"] == qn and a["sub_question_number"] == sub_qn:
                    original_answer = a["student_answer"]  # 기존 답안 백업
                    a["student_answer"] = result_string
                    print(f"     ✅ Q{qn}-{sub_qn}에 '{result_string}' 저장됨 (이전: '{original_answer}')")
                    found_answer = True
                    break
            
            if not found_answer:
                print(f"     ⚠️  Q{qn}-{sub_qn}에 해당하는 answer 슬롯을 찾을 수 없습니다!")
                print(f"       사용 가능한 슬롯들: {[(a['question_number'], a['sub_question_number']) for a in answer_json_studentAnswers['answers'][:5]]}...")

        print("")  # 빈 줄 추가

    print(f"🎯 2단계 완료 요약:")
    print(f"   - 처리된 문제 수: {len(grouped_answers_by_qn_and_subqn)}개")
    print(f"   - 총 추출된 숫자 컨투어: {total_digit_crops_count}개")
    print(f"   - answer_json_studentAnswers 답안 슬롯: {len(answer_json_studentAnswers['answers'])}개")
    print(f"   - 성공한 답안: {sum(1 for a in answer_json_studentAnswers['answers'] if a['student_answer'])}개")
    print(f"   - 실패한 이미지: {len(failure_json_images)}개")
    
    # 답안 저장 상태 점검
    print(f"\n📊 답안 저장 상태 점검:")
    saved_answers = [a for a in answer_json_studentAnswers['answers'] if a['student_answer']]
    empty_answers = [a for a in answer_json_studentAnswers['answers'] if not a['student_answer']]
    
    print(f"   ✅ 저장된 답안 ({len(saved_answers)}개):")
    for a in saved_answers:
        print(f"     Q{a['question_number']}-{a['sub_question_number']}: '{a['student_answer']}'")
    
    if empty_answers:
        print(f"   ❌ 비어있는 답안 ({len(empty_answers)}개):")
        for a in empty_answers[:5]:  # 처음 5개만 출력
            print(f"     Q{a['question_number']}-{a['sub_question_number']}: (비어있음)")
        if len(empty_answers) > 5:
            print(f"     ... 외 {len(empty_answers) - 5}개")
    
    if failure_json_images:
        print(f"   💥 실패한 문제들 ({len(failure_json_images)}개):")
        for fail in failure_json_images:
            reason = fail.get('failure_reason', '알 수 없음')
            print(f"     Q{fail['question_number']}-{fail['sub_question_number']}: {reason}")
    
    # 성공률 계산
    success_rate = (len(saved_answers) / len(answer_json_studentAnswers['answers'])) * 100 if answer_json_studentAnswers['answers'] else 0
    print(f"\n🎯 전체 성공률: {success_rate:.1f}% ({len(saved_answers)}/{len(answer_json_studentAnswers['answers'])})")
    
    # 신뢰도 기준으로 필터링된 결과 확인
    confidence_failures = [f for f in failure_json_images if f.get('failure_reason') == '신뢰도 부족']
    if confidence_failures:
        print(f"   📉 신뢰도 부족으로 실패: {len(confidence_failures)}개")
    
    recognition_failures = [f for f in failure_json_images if f.get('failure_reason') == '인식 불가']
    if recognition_failures:
        print(f"   🚫 인식 불가로 실패: {len(recognition_failures)}개")
    
    # 최종 결과 리턴
    return {
        "answer_json": answer_json_studentAnswers,
        "failure_json": failure_json_images
    }

    # return answer_json_studentAnswers, failure_json_images

if __name__ == "__main__":
    # preprocess_answer_sheet 함수 테스트

    # 인공지능 시험지
    # test_original_image_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer/32174515.jpg'
    # test_answer_key_json_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/test_answer.json'

    # 신호와 시스템 시험지(유석이가 제작 0605)
    test_original_image_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data_signals/신호및시스템_학생답안지 및 학적정보/final_test_image/32208925.jpg'
    test_answer_key_json_path = '/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data_signals/test_answer.json'

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

        # --- recognize_answer_sheet_data 함수 테스트 (1단계까지) ---
        print("\n--- Running Recognition Test (Step 1) --- ")
        # answer_key_data 로드 (recognize_answer_sheet_data 함수에 필요)
        try:
            with open(test_answer_key_json_path, 'r', encoding='utf-8') as f:
                answer_key_data_for_test = json.load(f)
            
            recognition_step1_result = recognize_answer_sheet_data(processed_crops, answer_key_data_for_test)
            print("\nRecognition Step 1 Result:")
            # 보기 쉽게 json.dumps를 사용하여 출력
            print(json.dumps(recognition_step1_result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error during recognition test (Step 1): {e}")

    print("\n--- Test Script Finished ---")
