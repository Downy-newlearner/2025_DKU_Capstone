from PIL import Image
import cv2

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

import numpy as np
from typing import List, Tuple, Dict, Any

# 이 파일의 함수들은 PIL Image와 OpenCV 객체를 주로 다루며, 
# 다른 프로젝트 모듈에 대한 직접적인 의존성은 현재 없어 보입니다.
# 만약 DetectedArea 같은 타입을 여기서도 사용한다면 from ..data_structures import DetectedArea 추가 필요.

def enhance_and_find_contours_for_lines(pil_image: Image.Image) -> List[Tuple[int, int, int, int]]:
    """
    이미지에서 수평선을 검출하여 바운딩 박스를 반환하는 함수
    
    주로 표나 문서에서 행을 구분하는 수평선들을 찾기 위해 사용됩니다.
    CLAHE 대비 개선, 모폴로지 연산을 통한 수평선 강화, 컨투어 검출을 순차적으로 수행합니다.
    
    Args:
        pil_image (Image.Image): 입력 PIL 이미지 객체
        
    Returns:
        List[Tuple[int, int, int, int]]: 검출된 수평선들의 바운딩 박스 리스트
                                        각 튜플은 (x, y, width, height) 형식
    
    Processing Steps:
        1. RGB 형식으로 변환 및 OpenCV 배열 변환
        2. 그레이스케일 변환
        3. CLAHE를 사용한 대비 개선 (clipLimit=2.0, tileGridSize=(8,8))
        4. 가우시안 블러로 노이즈 제거 (kernel_size=(5,5))
        5. OTSU 임계값을 사용한 이진화 (반전된 이진 이미지)
        6. 수평 커널을 사용한 모폴로지 오프닝으로 수평선 강화
        7. 컨투어 검출 및 크기 필터링
        
    Filtering Criteria:
        - 최소 너비: 이미지 너비의 1/6 이상
        - 최대 높이: 20픽셀 이하
        - 수평 커널 크기: max(15, 이미지너비/3)
    """
    # 1. 이미지 형식 정규화: RGB로 변환하여 일관된 처리 보장
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    cv_image = np.array(pil_image)
    
    # 2. 그레이스케일 변환: 색상 정보 제거하여 구조적 특징에 집중
    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
    
    # 3. CLAHE (Contrast Limited Adaptive Histogram Equalization) 적용
    # - 지역적 대비 개선으로 수평선 시각적 강화
    # - clipLimit=2.0: 과도한 대비 증가 방지
    # - tileGridSize=(8,8): 8x8 타일 단위로 적응적 히스토그램 평활화
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 4. 가우시안 블러: 노이즈 제거 및 이미지 평활화
    # - kernel_size=(5,5): 중간 정도의 블러링으로 세부 노이즈 제거
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # 5. 이진화: OTSU 방법으로 자동 임계값 결정
    # - THRESH_BINARY_INV: 전경(수평선)을 흰색(255)으로, 배경을 검은색(0)으로
    # - OTSU: 이미지 히스토그램을 분석하여 최적 임계값 자동 결정
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 6. 수평선 검출을 위한 모폴로지 연산
    # - 수평 커널 크기: 이미지 너비에 비례하되 최소 15픽셀 보장
    # - 가로로 긴 직사각형 커널로 수평 구조 강화
    horizontal_size = max(15, cv_image.shape[1] // 3)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    
    # - 모폴로지 오프닝: 침식 후 팽창으로 수평선만 남기고 다른 구조 제거
    # - iterations=1: 한 번의 오프닝 연산으로 적절한 필터링
    horizontal_lines_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    # 7. 컨투어 검출: 수평선들의 외곽선 추출
    # - RETR_EXTERNAL: 가장 바깥쪽 컨투어만 검출
    # - CHAIN_APPROX_SIMPLE: 컨투어 점 수를 최소화하여 메모리 효율성 향상
    contours, _ = cv2.findContours(horizontal_lines_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 8. 검출된 컨투어 필터링 및 바운딩 박스 추출
    detected_lines_bboxes = []
    min_line_width = cv_image.shape[1] // 6  # 최소 너비: 이미지 너비의 1/6
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 필터링 조건:
        # - 너비가 최소 기준 이상: 실제 수평선으로 판단할 수 있는 충분한 길이
        # - 높이가 20픽셀 이하: 선의 특성상 얇아야 함 (텍스트나 다른 객체 제외)
        if w >= min_line_width and h <= 20:
             detected_lines_bboxes.append((x, y, w, h))
             
    return detected_lines_bboxes

def enhance_and_find_contours_for_lines_v2(
    pil_image: Image.Image,
    kernel_size_ratio: float = 0.5,
    min_width_ratio: float = 0.2,
    max_height: int = 15,
    merge_threshold: int = 20,
    clahe_clip_limit: float = 2.0,
    use_adaptive_kernel: bool = True
) -> List[Tuple[int, int, int, int]]:
    """
    개선된 수평선 검출 함수 (v2)
    
    기존 함수와 line_detection.py의 검증된 로직을 결합하여 더 나은 성능과 유연성을 제공합니다.
    다양한 문서 타입과 이미지 품질에 적응할 수 있도록 파라미터를 조정 가능하게 설계했습니다.
    
    Args:
        pil_image (Image.Image): 입력 PIL 이미지 객체
        kernel_size_ratio (float): 수평 커널 크기 비율 (기본값: 0.5, 이미지 너비의 50%)
        min_width_ratio (float): 최소 선 너비 비율 (기본값: 0.2, 이미지 너비의 20%)  
        max_height (int): 수평선으로 인정할 최대 높이 (기본값: 15픽셀)
        merge_threshold (int): 가까운 y좌표 병합 임계값 (기본값: 20픽셀)
        clahe_clip_limit (float): CLAHE 클립 한계값 (기본값: 2.0)
        use_adaptive_kernel (bool): 적응적 커널 크기 사용 여부 (기본값: True)
        
    Returns:
        List[Tuple[int, int, int, int]]: 검출된 수평선들의 바운딩 박스 리스트
                                        각 튜플은 (x, y, width, height) 형식
    
    Improvements over v1:
        1. 파라미터 조정 가능: 다양한 문서 타입에 적응
        2. 적응적 커널 크기: 이미지 크기에 따른 동적 조정
        3. 향상된 필터링: line_detection.py의 검증된 기준 적용
        4. 좌표 병합 로직: 중복 선 제거 개선
        5. 성능 최적화: 불필요한 연산 제거
        
    Processing Algorithm:
        1. 이미지 전처리 (RGB 정규화, 그레이스케일)
        2. 적응적 CLAHE 대비 개선 
        3. 가우시안 블러 노이즈 제거
        4. OTSU 이진화
        5. 동적 크기 수평 커널 적용
        6. 모폴로지 오프닝으로 수평선 추출
        7. 지능형 컨투어 필터링
        8. 중복 제거 및 병합
    """
    # 1. 입력 검증 및 이미지 전처리
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    cv_image = np.array(pil_image)
    
    # 이미지 크기 검증
    img_height, img_width = cv_image.shape[:2]
    if img_height < 10 or img_width < 10:
        return []  # 너무 작은 이미지는 처리 불가
    
    # 2. 그레이스케일 변환
    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
    
    # 3. 향상된 CLAHE 적용 (line_detection.py 검증된 파라미터 적용)
    clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 4. 적응적 가우시안 블러 (이미지 크기에 따른 커널 조정)
    blur_size = max(3, min(7, img_width // 200))  # 이미지 크기에 비례한 블러 커널
    if blur_size % 2 == 0:  # 홀수로 맞추기
        blur_size += 1
    blurred = cv2.GaussianBlur(enhanced, (blur_size, blur_size), 0)
    
    # 5. OTSU 이진화 (검증된 방식 유지)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 6. 동적 수평 커널 크기 계산 (v1과 line_detection.py 방식 결합)
    if use_adaptive_kernel:
        # 적응적 방식: 이미지 크기와 비율을 고려
        base_kernel_size = int(img_width * kernel_size_ratio)
        horizontal_size = max(15, min(base_kernel_size, img_width // 2))
    else:
        # 고정 방식: line_detection.py 스타일
        horizontal_size = img_width // 2
    
    # 7. 수평선 강화 모폴로지 연산
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal_lines_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    # 8. 컨투어 검출
    contours, _ = cv2.findContours(horizontal_lines_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 9. 향상된 필터링 (line_detection.py의 검증된 기준 적용)
    detected_lines_bboxes = []
    min_line_width = int(img_width * min_width_ratio)  # 파라미터화된 최소 너비
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 개선된 필터링 조건:
        # 1. 최소 너비 검증 (line_detection.py 스타일: 더 관대한 기준)
        # 2. 최대 높이 검증 (더 엄격한 기준으로 정확도 향상)
        # 3. 가로세로 비율 검증 (새로 추가: 실제 선인지 확인)
        if w >= min_line_width and h <= max_height:
            aspect_ratio = w / h if h > 0 else float('inf')
            # 가로세로 비율이 최소 3:1 이상이어야 수평선으로 인정
            if aspect_ratio >= 3.0:
                detected_lines_bboxes.append((x, y, w, h))
    
    # 10. 중복 제거 및 Y좌표 병합 (line_detection.py 로직 개선)
    if not detected_lines_bboxes:
        return []
    
    # Y좌표 기준으로 정렬
    detected_lines_bboxes.sort(key=lambda bbox: bbox[1])
    
    # 가까운 Y좌표의 선들을 병합
    merged_lines = []
    current_line = detected_lines_bboxes[0]
    
    for next_line in detected_lines_bboxes[1:]:
        curr_y = current_line[1]
        next_y = next_line[1]
        
        # 병합 조건: Y좌표 차이가 임계값 이내
        if abs(next_y - curr_y) <= merge_threshold:
            # 더 긴 선을 선택하여 병합
            if next_line[2] > current_line[2]:  # width 비교
                current_line = next_line
        else:
            # 병합하지 않고 현재 선 저장
            merged_lines.append(current_line)
            current_line = next_line
    
    # 마지막 선 추가
    merged_lines.append(current_line)
    
    # 11. 최종 검증 및 정렬
    final_lines = []
    for line in merged_lines:
        x, y, w, h = line
        # 최종 검증: 너무 작거나 이상한 선 제거
        if w >= min_line_width * 0.8 and h <= max_height and w >= h * 2:
            final_lines.append(line)
    
    # X좌표 기준으로 정렬 (읽기 순서 고려)
    final_lines.sort(key=lambda bbox: (bbox[1], bbox[0]))  # Y좌표 우선, X좌표 보조
    
    return final_lines

def crop_between_lines(
    pil_image: Image.Image, 
    detected_lines_bboxes: List[Tuple[int,int,int,int]]
) -> List[Dict[str, Any]]: # [{'image_obj': Image, 'y_top_in_area': int, 'y_bottom_in_area': int}]
    line_y_coords = [0]
    for _, y_line, _, h_line in detected_lines_bboxes:
        line_y_coords.extend([y_line, y_line + h_line])
    line_y_coords.append(pil_image.height)
    line_y_coords = sorted(list(set(line_y_coords)))

    merged_y = []
    if line_y_coords:
        i = 0
        while i < len(line_y_coords):
            current = line_y_coords[i]
            j = i + 1
            while j < len(line_y_coords) and line_y_coords[j] - current < 25:
                j += 1
            merged_y.append(current)
            i = j
        line_y_coords = merged_y

    line_cropped_outputs: List[Dict[str, Any]] = []
    for i in range(len(line_y_coords) - 1):
        y_start, y_end = line_y_coords[i], line_y_coords[i+1]
        height = y_end - y_start
        if height < 15:
            continue
        
        # 위아래로 3픽셀씩 여유 공간 추가 (이미지 경계 체크)
        y_start_shrink = max(0, y_start + 3)
        y_end_shrink = min(pil_image.height, y_end - 3)
        
        cropped_pil = pil_image.crop((5, y_start_shrink, pil_image.width-15, y_end_shrink)) # 상하좌우 일부 픽셀을 잘라내서 표의 선이 잡히지 않도록 함 0610 다훈
        line_cropped_outputs.append({
            'image_obj': cropped_pil, 
            'y_top_in_area': y_start,  # 원래 y 좌표는 그대로 유지
            'y_bottom_in_area': y_end  # 원래 y 좌표는 그대로 유지
        })
    return line_cropped_outputs

def preprocess_line_image_for_text_contours(line_pil_image: Image.Image) -> List[np.ndarray]:
    if line_pil_image.mode != 'RGB':
        line_pil_image = line_pil_image.convert('RGB')
    cv_image = np.array(line_pil_image)
    if cv_image.shape[0] < 5 or cv_image.shape[1] < 5: return []

    # split_and_recognize_single_digits.py와 동일한 단순하고 효과적인 방법 사용
    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    return contours

def merge_contours_and_crop_text_pil(
    line_pil_image: Image.Image, 
    contours: List[np.ndarray],
    merge_distance_threshold: int = 100,
    padding: int = 5
) -> List[Dict[str, Any]]: # [{'image_obj': Image, 'x_in_line': int, 'y_in_line': int}]
    bounding_boxes_initial: List[Dict[str, Any]] = []
    img_width = line_pil_image.width
    img_height = line_pil_image.height
    
    # 빈 박스 필터링을 위한 그레이스케일 배열
    line_np_array = np.array(line_pil_image.convert('L'))
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 만약 w가 원본 이미지의 95% 이상이면 병합 대상에서 제외
        if w > 0.95 * img_width:
            continue

        # 만약 너무 작은 박스면 병합 대상에서 제외
        if w < 2 or h < 10:
            continue
        
        # 가로선(표의 일부) 제거 - 가로세로 비율이 너무 큰 것들 제거
        aspect_ratio = w / h
        if aspect_ratio > 1.8:  # 가로가 세로의 6배 이상이면 가로선으로 간주
            continue

        # if aspect_ratio < 0.5:
        #     continue
        
        # 빈 박스나 테두리만 있는 영역 제거 (과감하게 엄격함)
        roi = line_np_array[y:y+h, x:x+w]
        if roi.size > 0:
            # 검은 픽셀 비율 계산
            dark_pixels = np.sum(roi < 150)  # 180 → 120으로 과감하게 엄격
            total_pixels = roi.size
            dark_ratio = dark_pixels / total_pixels
            
            # 빈 영역 제외 조건을 과감하게 엄격하게
            if dark_ratio < 0.04:  # 1.5% → 5%로 과감하게 엄격
                continue
        
        bounding_boxes_initial.append({'x':x, 'y':y, 'w':w, 'h':h, 'xc': x + w/2, 'yc': y + h/2, 'merged': False})

    if not bounding_boxes_initial:
        return []

    bounding_boxes_initial.sort(key=lambda b: b['x'])
    
    merged_boxes_final: List[Dict[str, Any]] = []
    current_merged_box = None

    for i, box_info in enumerate(bounding_boxes_initial):
        if not current_merged_box:
            current_merged_box = box_info.copy()
            current_merged_box['merged_count'] = 1
            continue

        prev_xc, prev_yc = current_merged_box['xc'], current_merged_box['yc']
        curr_xc, curr_yc = box_info['xc'], box_info['yc']
        
        dist_x_centers = abs(curr_xc - prev_xc)
        y_overlap = max(current_merged_box['y'], box_info['y']) < min(current_merged_box['y'] + current_merged_box['h'], box_info['y'] + box_info['h'])

        if dist_x_centers < merge_distance_threshold and y_overlap:
            new_x = min(current_merged_box['x'], box_info['x'])
            new_y = min(current_merged_box['y'], box_info['y'])
            new_x_plus_w = max(current_merged_box['x'] + current_merged_box['w'], box_info['x'] + box_info['w'])
            new_y_plus_h = max(current_merged_box['y'] + current_merged_box['h'], box_info['y'] + box_info['h'])
            
            current_merged_box['x'] = new_x
            current_merged_box['y'] = new_y
            current_merged_box['w'] = new_x_plus_w - new_x
            current_merged_box['h'] = new_y_plus_h - new_y
            current_merged_box['xc'] = current_merged_box['x'] + current_merged_box['w'] / 2
            current_merged_box['yc'] = current_merged_box['y'] + current_merged_box['h'] / 2
            current_merged_box['merged_count'] +=1
        else:
            merged_boxes_final.append(current_merged_box)
            current_merged_box = box_info.copy()
            current_merged_box['merged_count'] = 1
            
    if current_merged_box:
        merged_boxes_final.append(current_merged_box)

    final_text_crop_outputs: List[Dict[str, Any]] = []
    for box_data in merged_boxes_final:
        x, y, w, h = box_data['x'], box_data['y'], box_data['w'], box_data['h']
        original_w = w
        original_h = h
        
        x_p = max(0, x - padding)
        y_p = max(0, y - padding)
        r_p = min(line_pil_image.width, x + w + padding)
        b_p = min(line_pil_image.height, y + h + padding)

        if r_p <= x_p or b_p <= y_p: continue

        text_crop_pil = line_pil_image.crop((x_p, y_p, r_p, b_p))
        
        target_w, target_h = text_crop_pil.width, text_crop_pil.height
        
        square_size = max(target_w, target_h)
        
        square_canvas_pil = Image.new('RGB', (square_size, square_size), (255, 255, 255))
        paste_x = (square_size - target_w) // 2
        paste_y = (square_size - target_h) // 2
        square_canvas_pil.paste(text_crop_pil, (paste_x, paste_y))
        
        final_text_crop_outputs.append({
            'image_obj': square_canvas_pil, 
            'x_in_line': x,
            'y_in_line': y,
            'original_w': original_w,
            'original_h': original_h
        })
        
    final_text_crop_outputs.sort(key=lambda item: item['x_in_line'])
    return final_text_crop_outputs 

def visualize_line_detection_comparison(
    pil_image: Image.Image, 
    save_path: str = None,
    test_both_versions: bool = True
) -> Dict[str, Any]:
    """
    수평선 검출 결과를 시각화하고 v1, v2 성능을 비교하는 함수
    
    Args:
        pil_image: 입력 PIL 이미지
        save_path: 저장할 경로 (None이면 저장하지 않음)
        test_both_versions: v1, v2 모두 테스트할지 여부
    
    Returns:
        Dict containing comparison results and statistics
    """
    import matplotlib.pyplot as plt
    import time
    
    results = {
        'v1': {'lines': [], 'time': 0, 'count': 0},
        'v2': {'lines': [], 'time': 0, 'count': 0}
    }
    
    # V1 테스트
    start_time = time.time()
    v1_lines = enhance_and_find_contours_for_lines(pil_image)
    results['v1']['time'] = time.time() - start_time
    results['v1']['lines'] = v1_lines
    results['v1']['count'] = len(v1_lines)
    
    if test_both_versions:
        # V2 테스트 (다양한 파라미터)
        start_time = time.time()
        v2_lines = enhance_and_find_contours_for_lines_v2(pil_image)
        results['v2']['time'] = time.time() - start_time
        results['v2']['lines'] = v2_lines
        results['v2']['count'] = len(v2_lines)
    
    # 시각화
    fig, axes = plt.subplots(1, 3 if test_both_versions else 2, figsize=(15, 5))
    
    # 원본 이미지
    axes[0].imshow(pil_image)
    axes[0].set_title('Original Image')
    axes[0].axis('off')
    
    # V1 결과
    img_v1 = np.array(pil_image.copy())
    for x, y, w, h in v1_lines:
        cv2.rectangle(img_v1, (x, y), (x+w, y+h), (0, 255, 0), 2)
    axes[1].imshow(img_v1)
    axes[1].set_title(f'V1: {results["v1"]["count"]} lines\nTime: {results["v1"]["time"]:.3f}s')
    axes[1].axis('off')
    
    if test_both_versions:
        # V2 결과
        img_v2 = np.array(pil_image.copy())
        for x, y, w, h in v2_lines:
            cv2.rectangle(img_v2, (x, y), (x+w, y+h), (255, 0, 0), 2)
        axes[2].imshow(img_v2)
        axes[2].set_title(f'V2: {results["v2"]["count"]} lines\nTime: {results["v2"]["time"]:.3f}s')
        axes[2].axis('off')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"비교 결과 저장: {save_path}")
    
    plt.show()
    
    return results

def debug_text_crop_pipeline(
    pil_image: Image.Image,
    save_dir: str = "/tmp/debug_crops",
    use_v2: bool = True
) -> Dict[str, Any]:
    """
    텍스트 크롭 파이프라인의 각 단계를 디버그하는 함수
    
    Args:
        pil_image: 입력 PIL 이미지
        save_dir: 중간 결과 저장 디렉토리
        use_v2: v2 함수 사용 여부
    
    Returns:
        Dict containing pipeline results and statistics
    """
    import os
    import matplotlib.pyplot as plt
    
    os.makedirs(save_dir, exist_ok=True)
    
    debug_info = {
        'input_size': (pil_image.width, pil_image.height),
        'steps': {}
    }
    
    print("🔍 텍스트 크롭 파이프라인 디버그 시작...")
    
    # Step 1: 수평선 검출
    print("  단계 1: 수평선 검출...")
    if use_v2:
        line_contours = enhance_and_find_contours_for_lines_v2(pil_image)
        method = "v2"
    else:
        line_contours = enhance_and_find_contours_for_lines(pil_image)
        method = "v1"
    
    debug_info['steps']['line_detection'] = {
        'method': method,
        'lines_found': len(line_contours),
        'lines': line_contours
    }
    
    # 수평선 시각화 저장
    img_with_lines = np.array(pil_image.copy())
    for x, y, w, h in line_contours:
        cv2.rectangle(img_with_lines, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(img_with_lines, f"y:{y}", (x, y-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
    
    plt.figure(figsize=(12, 8))
    plt.imshow(img_with_lines)
    plt.title(f'수평선 검출 결과 ({method}): {len(line_contours)}개 라인')
    plt.axis('off')
    plt.savefig(os.path.join(save_dir, '1_line_detection.png'), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Step 2: 라인별 크롭
    print("  단계 2: 라인별 크롭...")
    line_cropped_list = crop_between_lines(pil_image, line_contours)
    
    debug_info['steps']['line_cropping'] = {
        'lines_cropped': len(line_cropped_list),
        'crop_info': []
    }
    
    # 각 라인 크롭 저장
    for idx, line_crop_data in enumerate(line_cropped_list):
        line_image = line_crop_data['image_obj']
        y_top = line_crop_data['y_top_in_area']
        y_bottom = line_crop_data['y_bottom_in_area']
        
        crop_info = {
            'index': idx,
            'y_range': (y_top, y_bottom),
            'height': y_bottom - y_top,
            'size': (line_image.width, line_image.height)
        }
        debug_info['steps']['line_cropping']['crop_info'].append(crop_info)
        
        # 라인 이미지 저장
        line_save_path = os.path.join(save_dir, f'2_line_{idx:02d}_y{y_top}-{y_bottom}.png')
        line_image.save(line_save_path)
    
    # Step 3: 각 라인에서 텍스트 검출 및 크롭
    print("  단계 3: 텍스트 검출 및 크롭...")
    all_text_crops = []
    total_text_crops = 0
    
    debug_info['steps']['text_cropping'] = {
        'lines_processed': 0,
        'total_text_crops': 0,
        'line_details': []
    }
    
    for line_idx, line_crop_data in enumerate(line_cropped_list):
        line_image = line_crop_data['image_obj']
        
        # 텍스트 컨투어 검출
        text_contours = preprocess_line_image_for_text_contours(line_image)
        
        # 텍스트 크롭
        text_crops_in_line = merge_contours_and_crop_text_pil(line_image, text_contours)
        
        line_detail = {
            'line_index': line_idx,
            'contours_found': len(text_contours),
            'text_crops': len(text_crops_in_line),
            'crop_details': []
        }
        
        # 라인별 텍스트 크롭 결과 시각화
        fig, axes = plt.subplots(2, max(1, len(text_crops_in_line)), figsize=(4*max(1, len(text_crops_in_line)), 8))
        if len(text_crops_in_line) == 1:
            axes = axes.reshape(-1, 1)
        elif len(text_crops_in_line) == 0:
            axes = axes.reshape(-1, 1)
        
        # 원본 라인 이미지 (상단)
        for col in range(max(1, len(text_crops_in_line))):
            if col == 0:
                axes[0, col].imshow(line_image)
                axes[0, col].set_title(f'Line {line_idx} Original')
            else:
                axes[0, col].axis('off')
        
        # 개별 텍스트 크롭들 (하단)
        for text_idx, text_crop_data in enumerate(text_crops_in_line):
            text_crop_image = text_crop_data['image_obj']
            x_in_line = text_crop_data['x_in_line']
            
            crop_detail = {
                'text_index': text_idx,
                'x_position': x_in_line,
                'size': (text_crop_image.width, text_crop_image.height)
            }
            line_detail['crop_details'].append(crop_detail)
            
            if text_idx < axes.shape[1]:
                axes[1, text_idx].imshow(text_crop_image)
                axes[1, text_idx].set_title(f'Text {text_idx}\nx:{x_in_line}')
                axes[1, text_idx].axis('off')
            
            # 개별 텍스트 크롭 저장
            text_save_path = os.path.join(save_dir, f'3_line{line_idx:02d}_text{text_idx:02d}_x{x_in_line}.png')
            text_crop_image.save(text_save_path)
        
        # 남은 subplot들 숨기기
        for text_idx in range(len(text_crops_in_line), axes.shape[1]):
            axes[1, text_idx].axis('off')
        
        plt.tight_layout()
        plt.savefig(os.path.join(save_dir, f'3_line_{line_idx:02d}_text_crops.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
        debug_info['steps']['text_cropping']['line_details'].append(line_detail)
        total_text_crops += len(text_crops_in_line)
        all_text_crops.extend(text_crops_in_line)
    
    debug_info['steps']['text_cropping']['lines_processed'] = len(line_cropped_list)
    debug_info['steps']['text_cropping']['total_text_crops'] = total_text_crops
    
    # 요약 정보 출력
    print(f"\n📊 디버그 결과 요약:")
    print(f"  입력 이미지 크기: {debug_info['input_size']}")
    print(f"  수평선 검출: {debug_info['steps']['line_detection']['lines_found']}개")
    print(f"  라인 크롭: {debug_info['steps']['line_cropping']['lines_cropped']}개")
    print(f"  텍스트 크롭: {debug_info['steps']['text_cropping']['total_text_crops']}개")
    print(f"  결과 저장 위치: {save_dir}")
    
    return debug_info

if __name__ == "__main__":
    import os
    from pathlib import Path
    
    print("🚀 image_utils.py 디버그 및 테스트 시작")
    print("=" * 60)
    
    # 테스트 이미지 경로 설정 (실제 경로로 수정 필요)
    test_image_paths = [
        "/home/jdh251425/2025_DKU_Capstone/AI/student_id_recognition/extract_student_num/test_answer/학생 답지 - 7.jpg",
        "/home/jdh251425/2025_DKU_Capstone/AI/student_id_recognition/extract_student_num/test_answer/학생 답지 - 1.jpg",
        "/home/jdh251425/2025_DKU_Capstone/AI/student_id_recognition/extract_student_num/test_answer/학생 답지 - 9.jpg",
        # 추가 테스트 이미지들...
    ]
    
    # 결과 저장 디렉토리
    debug_base_dir = "/tmp/image_utils_debug"
    os.makedirs(debug_base_dir, exist_ok=True)
    
    print(f"📁 디버그 결과 저장 위치: {debug_base_dir}")
    
    for i, img_path in enumerate(test_image_paths):
        if not os.path.exists(img_path):
            print(f"⚠️ 이미지 파일이 존재하지 않습니다: {img_path}")
            continue
            
        print(f"\n🖼️ 테스트 이미지 {i+1}: {Path(img_path).name}")
        
        try:
            # 이미지 로드
            pil_image = Image.open(img_path)
            print(f"   이미지 크기: {pil_image.size}")
            
            # 현재 이미지용 디렉토리 생성
            img_debug_dir = os.path.join(debug_base_dir, f"test_{i+1}_{Path(img_path).stem}")
            os.makedirs(img_debug_dir, exist_ok=True)
            
            # 1. 수평선 검출 성능 비교
            print("   🔍 1. 수평선 검출 성능 비교...")
            comparison_results = visualize_line_detection_comparison(
                pil_image, 
                save_path=os.path.join(img_debug_dir, "line_detection_comparison.png"),
                test_both_versions=True
            )
            
            print(f"     V1: {comparison_results['v1']['count']}개 라인, {comparison_results['v1']['time']:.3f}초")
            print(f"     V2: {comparison_results['v2']['count']}개 라인, {comparison_results['v2']['time']:.3f}초")
            
            # 2. 전체 텍스트 크롭 파이프라인 디버그
            print("   🔧 2. 텍스트 크롭 파이프라인 디버그...")
            
            # V1으로 테스트
            print("     V1 함수로 테스트...")
            v1_debug_dir = os.path.join(img_debug_dir, "v1_pipeline")
            v1_results = debug_text_crop_pipeline(pil_image, v1_debug_dir, use_v2=False)
            
            # V2로 테스트
            print("     V2 함수로 테스트...")
            v2_debug_dir = os.path.join(img_debug_dir, "v2_pipeline")
            v2_results = debug_text_crop_pipeline(pil_image, v2_debug_dir, use_v2=True)
            
            # 결과 비교
            print(f"\n   📊 파이프라인 결과 비교:")
            print(f"     V1 - 라인: {v1_results['steps']['line_detection']['lines_found']}개, "
                  f"텍스트: {v1_results['steps']['text_cropping']['total_text_crops']}개")
            print(f"     V2 - 라인: {v2_results['steps']['line_detection']['lines_found']}개, "
                  f"텍스트: {v2_results['steps']['text_cropping']['total_text_crops']}개")
            
        except Exception as e:
            print(f"   ❌ 오류 발생: {e}")
            continue
    
    print(f"\n🎉 테스트 완료!")
    print(f"📁 모든 결과는 다음 위치에 저장되었습니다: {debug_base_dir}")
    print("\n💡 사용법:")
    print("  - 각 test_X 폴더에서 단계별 결과 확인")
    print("  - line_detection_comparison.png: V1 vs V2 성능 비교")
    print("  - v1_pipeline/, v2_pipeline/: 각 버전별 상세 디버그 결과")
    print("  - 1_line_detection.png: 수평선 검출 결과")
    print("  - 2_line_XX.png: 개별 라인 크롭 결과")
    print("  - 3_line_XX_text_crops.png: 텍스트 크롭 결과") 