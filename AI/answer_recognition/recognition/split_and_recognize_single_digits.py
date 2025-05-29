'''
Written by 정다훈 (2025.05.02)
Last Updated by 정다훈 (2025.05.25)

이 파일의 함수들은 Text crop 이미지 뭉치로부터 각 이미지의 개별 숫자를 인식하고,
이를 조합하여 최종 답안을 추출하는 것을 목표로 합니다.

주요 기능:
- `generate_bounding_boxes_from_text_crop`: Text crop 이미지에서 숫자 영역의 바운딩 박스를 생성합니다.
- `recognize_images_from_bounding_boxes`: 바운딩 박스 내의 이미지를 숫자 분류 모델로 인식합니다.
- `split_and_recognize_single_digits`: 메인 함수로, 디렉토리 내의 여러 Text crop 이미지들을
  처리하여 각 원본 답안지별로 인식 성공/실패 여부와 인식된 답안(또는 실패 정보)을 반환합니다.
  인식 실패 정보는 별도의 JSON 파일에도 로깅될 수 있습니다.

최종적으로 `split_and_recognize_single_digits` 함수는 각 원본 답안지 이미지 세트(sub_dir)에 대한
인식 결과를 담은 딕셔너리를 반환합니다. 이 딕셔너리에는 성공/실패 상태,
성공 시 인식된 답안 리스트, 실패 시 실패 이유 및 관련 crop 이미지 정보가 포함됩니다.
(이전 버전에서는 CSV 파일 저장을 목표로 했으나, 현재는 구조화된 딕셔너리 반환 및 JSON 로깅 중심으로 변경됨)

split_and_recognize_single_digits 함수:
Param:
 - directory_path(answer text_crop imgs 폴더 경로)

Return:
 -  인식 결과 csv 저장


'''

import cv2
from transformers import pipeline
from PIL import Image
import pandas as pd
import os
import json

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

# text crop 이미지를 넣으면 bb를 만들어주는 함수
def generate_bounding_boxes_from_text_crop(text_crop_image_path):
    # 이미지 읽기
    image = cv2.imread(text_crop_image_path)
    
    # 그레이스케일로 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 이진화
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 컨투어 찾기
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 바운딩 박스 생성
    bounding_boxes = [cv2.boundingRect(contour) for contour in contours]
    
    return bounding_boxes

# 모델 로드 (애플리케이션 시작 시 한 번만 로드하는 것이 효율적일 수 있음)
# 파이프라인 초기화는 시간이 걸릴 수 있으므로, 모듈 로드 시 또는 클래스 초기화 시 수행하는 것이 좋음
try:
    pipe = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)
except Exception as e:
    print(f"Error initializing classification model: {e}")
    pipe = None

# bb들을 이미지로 만들어, 이미지를 인식하는 함수
# image_num은 이미지 파일에서 몇 번째 이미지인지를 나타내는 숫자이다.
def recognize_images_from_bounding_boxes(text_crop_image_path, bounding_boxes, image_num):
    if pipe is None:
        return {'status': 'failure', 'reason': 'Classification model not loaded', 'image_path': text_crop_image_path, 'data': []}

    image = cv2.imread(text_crop_image_path)
    if image is None:
        return {'status': 'failure', 'reason': f'Could not read image {text_crop_image_path}', 'image_path': text_crop_image_path, 'data': []}

    recognition_results_data = []
    all_successful = True

    for (x, y, w, h) in bounding_boxes:
        cropped_image = image[y:y+h, x:x+w]
        if cropped_image.size == 0:
            # print(f"Warning: Empty cropped image from {text_crop_image_path} at bbox {x},{y},{w},{h}")
            # 빈 이미지지만, 다른 박스 처리를 위해 에러로 간주하지 않고 넘어갈 수 있음. 또는 실패로 처리.
            # 여기서는 일단 이 박스는 건너뛰도록 처리하지 않음. 필요시 실패로 간주.
            continue # 또는 실패로 기록

        cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)).convert('RGB')
        
        try:
            predictions = pipe(cropped_pil_image)
        except Exception as e:
            # print(f"Error during model prediction for {text_crop_image_path}: {e}")
            return {'status': 'failure', 'reason': f'Model prediction error: {e}', 'image_path': text_crop_image_path, 'data': []}

        if predictions:
            top_prediction = predictions[0]
            text, confidence = top_prediction['label'], top_prediction['score']
            if confidence > 0.85: # 신뢰도 임계값
                recognition_results_data.append(((x + w//2, y + h//2), text, image_num))
            else:
                all_successful = False
                # 실패 사유를 더 구체적으로 전달할 수 있음
                recognition_results_data.append(((x + w//2, y + h//2), 'JSON_LOW_CONF', image_num)) 
                # print(f"Low confidence ({confidence:.2f}) for a digit in {text_crop_image_path}")
                # 전체 이미지에 대한 실패로 처리하기 위해 여기서 즉시 반환할 수 있음
                return {'status': 'failure', 'reason': f'Low confidence ({confidence:.2f}) for a digit', 'image_path': text_crop_image_path, 'data': recognition_results_data}
        else:
            all_successful = False
            recognition_results_data.append(((x + w//2, y + h//2), 'JSON_NO_PRED', image_num))
            # print(f"No prediction for a digit in {text_crop_image_path}")
            return {'status': 'failure', 'reason': 'No prediction for a digit', 'image_path': text_crop_image_path, 'data': recognition_results_data}

    if not recognition_results_data and bounding_boxes: # 박스는 있었는데 결과가 없는 경우
         return {'status': 'failure', 'reason': 'No digits processed despite bounding boxes', 'image_path': text_crop_image_path, 'data': []}
    if not bounding_boxes: # 박스가 아예 없었던 경우
        # 이걸 실패로 볼지, 아니면 그냥 빈 결과로 볼지는 정책에 따라 다름
        # print(f"No bounding boxes found in {text_crop_image_path}")
        pass # 일단 성공으로 간주하고 빈 데이터 반환

    recognition_results_data.sort(key=lambda item: item[0][0]) # x 좌표 기준으로 정렬
    return {'status': 'success', 'data': recognition_results_data}

# recognition_results는 각 바운딩 박스의 중심점과 인식된 텍스트로 구성된 리스트입니다.
# 각 항목은 ((x_center, y_center), text) 형태로 되어 있으며,
# x_center와 y_center는 바운딩 박스의 중심 좌표를 나타내고,
# text는 인식된 텍스트 또는 'JSON' (인식 실패 시)입니다.

def calculate_euclidean_distance(recognition_results1, recognition_results2):
    distance = 0
    for i in range(len(recognition_results1)):
        distance += ((recognition_results1[i][0][0] - recognition_results2[i][0][0]) ** 2 + (recognition_results1[i][0][1] - recognition_results2[i][0][1]) ** 2) ** 0.5
    return distance






# cropped_datasets/text_crop 폴더는 answer, question_number로 구성된다.
# 이 함수는 answer 폴더를 입력받는다고 가정하고 설계된다.
# 리턴은 pandas dataframe이다. 컬럼명은 다음과 같다.
    # name: 이미지 파일명
    # recognition_result: 인식 결과
    # 인식 결과의 데이터 종류는 다음과 같다.
        # 인식 성공(인식 결과가 값으로 표시됨)
        # 인식 실패('JSON' 이라는 문자열로 표시됨)

def split_and_recognize_single_digits(directory_path, failed_recognition_json_path):
    """
    디렉토리 내의 전처리된 답안 이미지들에서 개별 숫자를 인식하고 조합하여 답을 추출합니다.

    Args:
        directory_path (str): 전처리된 답안 이미지들이 있는 디렉토리 경로.
                              (예: .../cropped_datasets/text_crop_new/answer)
                              이 디렉토리 하위에는 원본 답안지별 폴더(sub_dir)가 있고,
                              그 안에 x_좌표별로 잘린 text crop 이미지 파일들이 있어야 합니다.
                              각 text crop 이미지 파일명에는 '_ac_N' 형태의 정답 개수 정보가
                              포함되어 있을 것으로 예상합니다.
        failed_recognition_json_path (str): 인식 실패 정보를 저장할 JSON 파일 경로.
                                           이 파일에는 처리에 실패한 crop 이미지들의 정보가
                                           원본 답안지(sub_dir)별로 기록됩니다.

    Returns:
        dict: 각 원본 답안지(sub_dir)를 키로 하고, 해당 답안지의 전체 인식 처리 결과를
              값으로 하는 딕셔너리를 반환합니다.
              각 값(딕셔너리)은 다음 키들을 가질 수 있습니다:
              - "status" (str): "success" 또는 "failure" 또는 "skipped".
              - "recognized_answers" (List[int]): "status"가 "success"일 때, 최종적으로 인식된 답안들의 리스트.
                                                (예: [12, 3, 45])
              - "reason" (str): "status"가 "failure" 또는 "skipped"일 때, 실패 또는 건너뛴 이유.
              - "failed_crops" (List[dict]): "status"가 "failure"이고, 개별 crop 이미지 처리 중
                                           실패가 있었을 경우, 실패한 crop 이미지의 경로와 이유를 담은
                                           딕셔셔리 리스트.
                                           (예: [{"path": "...", "reason": "Low confidence..."}])
              예시 반환 값:
              {
                  "answer_paper_001_id_123_y1_y2": { # sub_dir 이름
                      "status": "success",
                      "recognized_answers": [10, 25, 3]
                  },
                  "answer_paper_002_id_456_y3_y4": {
                      "status": "failure",
                      "reason": "One or more text crops failed processing",
                      "failed_crops": [
                          {"path": ".../crop_x1.jpg", "reason": "Low confidence (0.75) for a digit"},
                          {"path": ".../crop_x2.jpg", "reason": "No bounding boxes found"}
                      ]
                  },
                  "other_folder_not_answer_crops": {
                      "status": "skipped",
                      "reason": "Images missing 'ac_' in name"
                  }
              }
    """
    all_results = {} # 모든 sub_dir에 대한 결과를 저장할 딕셔너리
    failed_log_data = {} # JSON 파일에 저장할 실패 로그

    if not os.path.exists(directory_path):
        print(f"Error: Directory not found - {directory_path}")
        return {} # 빈 결과 반환

    if os.path.exists(failed_recognition_json_path) and os.stat(failed_recognition_json_path).st_size > 0:
        try:
            with open(failed_recognition_json_path, 'r') as f:
                failed_log_data = json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: Could not decode existing JSON from {failed_recognition_json_path}. Starting fresh.")
            failed_log_data = {}
    else:
        failed_log_data = {}

    sub_dirs = [d for d in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, d))]
    
    # sub_dirs 리스트는 각 이름의 첫 번째 언더스코어('_') 뒤에 있는 숫자를 기준으로 정렬 (원본 이미지 순서대로 처리하기 위함)
    try:
        sub_dirs.sort(key=lambda x: int(x.split('_')[1]))
    except (IndexError, ValueError) as e:
        print(f"Warning: Could not sort sub_dirs based on number: {e}. Using default OS order.")


    for sub_dir in sub_dirs:
        sub_dir_path = os.path.join(directory_path, sub_dir)
        image_files = [f for f in os.listdir(sub_dir_path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

        if not image_files:
            all_results[sub_dir] = {'status': 'failure', 'reason': 'No image files found in sub_dir'}
            continue

        # 파일명에 'ac_' (answer_counts) 정보가 있는지 확인. 없다면 답안 text_crop 이미지가 아닐 수 있음.
        if 'ac_' not in image_files[0]:
            # print(f"Skipping sub_dir {sub_dir} as images do not seem to be answer crops (missing 'ac_').")
            all_results[sub_dir] = {'status': 'skipped', 'reason': "Images missing 'ac_' in name"}
            continue
        
        # text_crop 이미지들을 x 좌표 기준으로 정렬
        try:
            image_files.sort(key=lambda x: int((x.split('x_')[1]).split('_')[0]))
        except (IndexError, ValueError) as e:
            print(f"Warning: Could not sort image_files in {sub_dir} by x-coordinate: {e}. Processing in default order.")
            all_results[sub_dir] = {'status': 'failure', 'reason': f'Failed to sort image files: {e}'}
            continue

        results_about_all_crops_for_one_answer = [] # 현재 sub_dir의 모든 text_crop 이미지 인식 결과 (성공 시)
        current_sub_dir_failed_crops = [] # 현재 sub_dir에서 실패한 crop 정보
        overall_status_for_sub_dir = 'success' # sub_dir의 전체적인 처리 상태

        # image_num은 해당 sub_dir 내에서 몇 번째 text_crop 이미지인지를 나타냄
        for image_idx, text_crop_filename in enumerate(image_files):
            text_crop_image_path = os.path.join(sub_dir_path, text_crop_filename)
            bounding_boxes = generate_bounding_boxes_from_text_crop(text_crop_image_path)

            if not bounding_boxes:
                # print(f"No bounding boxes for {text_crop_image_path}. Skipping this crop.")
                # 이 경우, 이 crop은 결과에 포함되지 않음. 전체 sub_dir 실패로 이어질 수 있음.
                current_sub_dir_failed_crops.append({'path': text_crop_image_path, 'reason': 'No bounding boxes found'})
                overall_status_for_sub_dir = 'failure' # 하나의 크롭이라도 실패하면 sub_dir 실패로 간주할 수 있음
                continue # 다음 text_crop 이미지로

            recognition_output = recognize_images_from_bounding_boxes(text_crop_image_path, bounding_boxes, image_idx + 1)

            if recognition_output['status'] == 'success':
                if recognition_output['data']: # 데이터가 있는 경우에만 추가
                    results_about_all_crops_for_one_answer.append(recognition_output['data'])
                # else: 빈 데이터지만 성공인 경우 (예: 박스 탐지 안됨) 그냥 넘어감
            else: # 인식 실패
                overall_status_for_sub_dir = 'failure'
                current_sub_dir_failed_crops.append({
                    'path': text_crop_image_path,
                    'reason': recognition_output.get('reason', 'Unknown recognition error')
                })
                # 하나의 crop이라도 실패하면 이 sub_dir의 처리를 중단할 수 있음 (정책에 따라)
                # break # 여기서는 계속 진행하여 모든 실패를 기록

        if overall_status_for_sub_dir == 'failure':
            all_results[sub_dir] = {'status': 'failure', 'reason': 'One or more text crops failed processing', 'failed_crops': current_sub_dir_failed_crops}
            if sub_dir not in failed_log_data:
                failed_log_data[sub_dir] = []
            failed_log_data[sub_dir].extend(current_sub_dir_failed_crops)
            continue # 다음 sub_dir로

        if not results_about_all_crops_for_one_answer:
            all_results[sub_dir] = {'status': 'failure', 'reason': 'No successful recognitions from any text crops'}
            if sub_dir not in failed_log_data:
                failed_log_data[sub_dir] = []
            failed_log_data[sub_dir].append({'path': sub_dir_path, 'reason': 'No successful recognitions'})
            continue


        # --- 여기서부터는 results_about_all_crops_for_one_answer (모든 크롭 성공) 기반으로 숫자 조합 로직 ---
        # results_about_all_crops_for_one_answer 는 [[((x,y),'digit',img_idx),...], [((x,y),'digit',img_idx),...]] 형태
        
        # 유클리드 거리 계산 (한 크롭 내 숫자 간 거리)
        # 이 로직은 한 text_crop 이미지 내에 여러 숫자가 있을 때 그 숫자들을 연결할지 분리할지 결정하는데 사용됨
        euclidean_distances = []
        for crop_idx, single_crop_results in enumerate(results_about_all_crops_for_one_answer):
            for i in range(len(single_crop_results) - 1):
                entity1, entity2 = single_crop_results[i], single_crop_results[i+1]
                coordinate1, coordinate2 = entity1[0], entity2[0] # (x_center, y_center)
                distance = ((coordinate1[0] - coordinate2[0]) ** 2 + (coordinate1[1] - coordinate2[1]) ** 2) ** 0.5
                euclidean_distances.append({'distance': distance, 'crop_index': crop_idx, 'digit_index_in_crop': i})
        
        euclidean_distances.sort(key=lambda x: x['distance'], reverse=True)

        # 답안 개수 정보 (ac_N) 가져오기. N이 답의 개수.
        # image_files가 비어있지 않음은 위에서 확인됨.
        try:
            answer_count_str = image_files[0].split('_ac_')[1][0]
            num_expected_answers = int(answer_count_str)
            if num_expected_answers == 0 and 'ac_0' in image_files[0]: # 'ac_0'은 보통 단일 답을 의미
                num_expected_answers = 1 
        except (IndexError, ValueError) as e:
            print(f"Warning: Could not parse answer count from filename in {sub_dir}. Defaulting to 1. Error: {e}")
            num_expected_answers = 1 # 기본값 또는 오류 처리

        # 인식된 숫자 덩어리(text crop 이미지)의 개수
        num_recognized_digit_groups = len(results_about_all_crops_for_one_answer)
        
        # 끊어야 할 횟수: 예상 답 개수와 인식된 그룹 수의 차이. 음수면 0.
        # 이 로직은 예상 답 개수보다 적은 그룹으로 숫자들이 인식되었을 때,
        # 멀리 떨어진 숫자들을 분리하여 예상 답 개수에 맞추려는 시도로 보임.
        num_disconnects_needed = max(0, num_expected_answers - num_recognized_digit_groups)

        # 숫자 조합 로직 (기존 코드 기반으로 재구성 시도)
        # 이 부분은 원본 코드의 의도를 최대한 살리되, 명확성을 높이는 방향으로 개선 필요
        final_recognized_numbers = []
        current_number_str = ""

        for crop_idx, single_crop_recognition_data in enumerate(results_about_all_crops_for_one_answer):
            # single_crop_recognition_data: [((x,y),'digit',img_idx), ...]
            # 각 crop 내의 숫자들을 x좌표 기준으로 이미 정렬되어 있음 (recognize_images_from_bounding_boxes에서)
            
            temp_num_str_for_crop = ""
            for digit_info_idx, digit_info in enumerate(single_crop_recognition_data):
                # digit_info: ((x,y), 'recognized_digit_char', original_crop_image_num)
                temp_num_str_for_crop += digit_info[1] # 인식된 숫자 문자열을 이어붙임
                
                # 현재 숫자와 다음 숫자 사이에 끊어야 하는지 확인
                # num_disconnects_needed > 0 이고, 현재 위치가 가장 멀리 떨어진 지점 중 하나라면 끊음
                should_disconnect_here = False
                if num_disconnects_needed > 0 and euclidean_distances:
                    # 가장 먼 거리부터 확인
                    # `euclidean_distances`의 `crop_index`와 `digit_index_in_crop`이 현재 위치와 일치하는지 확인
                    for dist_info in euclidean_distances[:num_disconnects_needed]: # 가장 먼 N개만 고려
                        if dist_info['crop_index'] == crop_idx and dist_info['digit_index_in_crop'] == digit_info_idx:
                            should_disconnect_here = True
                            break
                
                if should_disconnect_here:
                    if temp_num_str_for_crop:
                        try:
                            final_recognized_numbers.append(int(temp_num_str_for_crop))
                        except ValueError:
                            # print(f"Warning: Could not convert '{temp_num_str_for_crop}' to int for {sub_dir}")
                            # 실패로 처리하거나, 문자열 그대로 넣거나, 특정 값으로 대체
                            pass # 또는 오류 기록
                    temp_num_str_for_crop = "" # 숫자 초기화
                    num_disconnects_needed -=1 # 끊었으므로 필요한 끊김 횟수 감소

            if temp_num_str_for_crop: # crop 내 마지막 숫자 처리
                 current_number_str += temp_num_str_for_crop
            
            # 각 crop 이미지가 하나의 답을 구성한다고 가정하고, crop 처리 후 숫자를 추가할 수 있음
            # 또는 모든 crop의 숫자를 모아서 `num_expected_answers`에 맞게 나누는 로직 필요
            # 원본 로직은 복잡하여, 여기서는 단순화된 접근: 각 crop 결과를 일단 모으고,
            # 만약 `num_expected_answers`와 `num_recognized_digit_groups`가 다르면 추가 처리.
            # 현재는 위에서 유클리드 거리 기반으로 분리 시도함.
            # 좀 더 명확한 분리/결합 규칙이 필요.

        if current_number_str: # 마지막으로 남은 숫자 처리
            try:
                final_recognized_numbers.append(int(current_number_str))
            except ValueError:
                # print(f"Warning: Could not convert final '{current_number_str}' to int for {sub_dir}")
                pass

        # 만약 final_recognized_numbers가 비어있는데, results_about_all_crops_for_one_answer는 내용이 있었다면, 숫자 조합 실패
        if not final_recognized_numbers and results_about_all_crops_for_one_answer:
            all_results[sub_dir] = {'status': 'failure', 'reason': 'Failed to combine recognized digits into final numbers'}
            if sub_dir not in failed_log_data: failed_log_data[sub_dir] = []
            failed_log_data[sub_dir].append({'path': sub_dir_path, 'reason': 'Digit combination failed'})
        else:
            all_results[sub_dir] = {'status': 'success', 'recognized_answers': final_recognized_numbers}

    # 모든 처리가 끝난 후 실패 로그를 JSON 파일에 한 번만 저장
    try:
        with open(failed_recognition_json_path, 'w') as f:
            json.dump(failed_log_data, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing failed recognition log to {failed_recognition_json_path}: {e}")

    return all_results

if __name__ == '__main__':
    # 테스트를 위한 예시 경로 설정
    # 실제 환경에서는 이 경로들을 인자로 받거나 설정 파일에서 읽어와야 합니다.
    # 테스트용 cropped_datasets/text_crop_new/answer 디렉토리 구조가 필요합니다.
    # 예: workspace_root/Algorithm/OCR/cropped_datasets/text_crop_new/answer/answer_1_y1_y2.jpg/crop1_x_..._ac_N.jpg
    
    # 현재 파일의 위치를 기준으로 상대 경로 구성 시도
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root_approx = os.path.abspath(os.path.join(current_script_dir, "..", "..", "..")) # AI 폴더까지 추정

    test_directory_path = os.path.join(workspace_root_approx, "Algorithm/OCR/cropped_datasets/text_crop_new/answer")
    test_failed_json_path = os.path.join(workspace_root_approx, "Algorithm/OCR/ocr_results/JSON/test_recog_failed.json")

    print(f"Testing with directory: {test_directory_path}")
    print(f"Failed log will be at: {test_failed_json_path}")

    if not os.path.exists(test_directory_path):
        print(f"Test directory not found: {test_directory_path}")
        print("Please ensure the test directory exists and contains sample data.")
    else:
        # ocr_results/JSON 폴더가 없으면 생성
        os.makedirs(os.path.dirname(test_failed_json_path), exist_ok=True)
        
        recognition_output = split_and_recognize_single_digits(test_directory_path, test_failed_json_path)
        
        print("\n--- 인식 결과 ---")
        print(json.dumps(recognition_output, indent=2, ensure_ascii=False))

        # CSV 저장 예시 (필요시 주석 해제)
        # output_csv_path = os.path.join(workspace_root_approx, "Algorithm/OCR/ocr_results/test_recognition_summary.csv")
        # if recognition_output:
        #     rows = []
        #     for sub_dir_name, data in recognition_output.items():
        #         if data['status'] == 'success':
        #             rows.append({'ImageSet': sub_dir_name, 'RecognizedAnswers': ','.join(map(str, data['recognized_answers'])), 'Status': 'Success', 'Details': ''})
        #         else:
        #             details = data.get('reason', '')
        #             if 'failed_crops' in data:
        #                 details += " Failed crops: " + str(len(data['failed_crops']))
        #             rows.append({'ImageSet': sub_dir_name, 'RecognizedAnswers': '', 'Status': 'Failure', 'Details': details})
            
        #     if rows:
        #         df = pd.DataFrame(rows)
        #         try:
        #             df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
        #             print(f"\nCSV summary saved to: {output_csv_path}")
        #         except Exception as e:
        #             print(f"Error saving CSV: {e}")
        # else:
        #     print("No output to save to CSV.")


'''
체크리스트
1. 답이 여러개인 경우
2. 답이 여러개인데 답 간의 간격이 특이한 경우
3. 답이 여러 글자인 경우
4. 글자가 겹쳐있는 경우
5. 답이 여러 글자이고 여러 개인 경우
6. 1, 4 조합


위 경우를 2(a)부터 3번까지 담아서 예시 이미지를 만들었다.

'''