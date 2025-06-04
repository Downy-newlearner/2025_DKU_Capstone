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
    if pil_image.mode != 'RGB':
        pil_image = pil_image.convert('RGB')
    cv_image = np.array(pil_image)
    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    horizontal_size = max(15, cv_image.shape[1] // 3)
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal_lines_mask = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    contours, _ = cv2.findContours(horizontal_lines_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    detected_lines_bboxes = []
    min_line_width = cv_image.shape[1] // 6
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        if w >= min_line_width and h <= 20:
             detected_lines_bboxes.append((x, y, w, h))
    return detected_lines_bboxes

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
        
        cropped_pil = pil_image.crop((0, y_start, pil_image.width, y_end))
        line_cropped_outputs.append({
            'image_obj': cropped_pil, 
            'y_top_in_area': y_start,
            'y_bottom_in_area': y_end
        })
    return line_cropped_outputs

def preprocess_line_image_for_text_contours(line_pil_image: Image.Image) -> List[np.ndarray]:
    if line_pil_image.mode != 'RGB':
        line_pil_image = line_pil_image.convert('RGB')
    cv_image = np.array(line_pil_image)
    if cv_image.shape[0] < 5 or cv_image.shape[1] < 5: return []

    gray = cv2.cvtColor(cv_image, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 9, 2)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def merge_contours_and_crop_text_pil(
    line_pil_image: Image.Image, 
    contours: List[np.ndarray],
    merge_distance_threshold: int = 40,
    padding: int = 5
) -> List[Dict[str, Any]]: # [{'image_obj': Image, 'x_in_line': int, 'y_in_line': int}]
    bounding_boxes_initial: List[Dict[str, Any]] = []
    img_width = line_pil_image.width
    img_height = line_pil_image.height
    
    # PIL 이미지를 numpy 배열로 변환 (텍스트 밀도 체크용)
    line_np_array = np.array(line_pil_image.convert('L'))  # 그레이스케일로 변환
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        
        # 기본 크기 및 비율 필터링 (조건 완화)
        if (w > 0.90 * img_width or w < 8 or h < 8 or 
            w > 8 * h or h > 8 * w):
            continue
            
        # 면적 기반 필터링 (조건 완화)
        area = w * h
        if area < 50:  # 최소 50 픽셀 면적으로 완화
            continue
            
        # 텍스트 밀도 체크 (조건 완화)
        # 해당 영역의 검은 픽셀 비율을 계산
        roi = line_np_array[y:y+h, x:x+w]
        if roi.size > 0:
            # 임계값을 통해 검은/흰 픽셀 구분 (128 이하를 검은색으로 간주)
            dark_pixels = np.sum(roi < 128)
            total_pixels = roi.size
            dark_ratio = dark_pixels / total_pixels
            
            # 검은 픽셀 비율이 너무 낮으면 (텍스트가 거의 없으면) 제외 (조건 완화)
            if dark_ratio < 0.005:  # 0.5% 미만의 검은 픽셀로 완화
                continue
                
            # 검은 픽셀 비율이 너무 높으면 (표나 선일 가능성) 제외
            if dark_ratio > 0.9:  # 90% 이상의 검은 픽셀로 완화
                continue
        
        # 컨투어 복잡도 체크 (조건 완화)
        contour_area = cv2.contourArea(contour)
        contour_perimeter = cv2.arcLength(contour, True)
        if contour_perimeter > 0:
            # 원형도 계산 (4π * 면적 / 둘레²)
            # 값이 1에 가까울수록 원에 가까움
            circularity = 4 * np.pi * contour_area / (contour_perimeter * contour_perimeter)
            # 너무 원형이거나 너무 복잡한 모양 제거 (범위 확대)
            if circularity > 0.95 or circularity < 0.05:
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
        
        # 최종 크기 체크 (조건 완화)
        if text_crop_pil.width < 10 or text_crop_pil.height < 10:
            continue
        
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