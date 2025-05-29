'''
Written by 정다훈 in 2025-04-12

이전의 contour 병합 로직을 개선하여 bounding box 병합 로직으로 전환합니다.

새로운 로직:

1. 각 contour를 cv2.boundingRect() 함수를 사용하여 바운딩 박스로 변환합니다. 변환된 bounding box의 x, y, w, h와 중심 좌표인 x_center, y_center를 계산하여 저장합니다.
2. 다음 세 가지 경우의 유클리드 거리를 계산하여, 하나라도 임계값 30 이하인 경우 bounding box를 병합합니다.

첫 번째 bb - 두 번째 bb
(x, y) - (x_center, y_center)
(x_center, y_center) - (x_center, y_center)
(x+w, y+h) - (x_center, y_center)

bounding box 병합 방법:
	• 두 bb의 x와 x+w를 비교하여, 더 작은 x 값을 병합된 bb의 x로, 더 큰 x+w 값을 병합된 bb의 x+w로 설정합니다. 병합된 bb는 x, y, w, h 값만 저장합니다.
	• 마찬가지로 두 bb의 y와 y+h를 비교하여, 더 작은 y 값을 병합된 bb의 y로, 더 큰 y+h 값을 병합된 bb의 y+h로 설정합니다.
	• 병합된 bb의 w는 (x+w) - x, h는 (y+h) - y로 계산합니다.
	• 최종적으로 병합된 bounding box는 두 box의 전체 영역을 포함하는 가장 외곽의 사각형이 됩니다.
'''

import cv2
import numpy as np
import os

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

# 새로운 병합 로직 함수
def merge_contours_v2(contours, merge_distance_threshold=50, output_dir=None, img=None): # output_dir, img는 디버깅 용도
    # 바운딩 박스 정보 저장
    bounding_boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        # 만약 w가 원본 이미지의 95% 이상이면 병합 대상에서 제외
        if w > 0.95 * img.shape[1]:
            continue

        # 만약 너무 작은 박스면 병합 대상에서 제외
        if w < 10 or h < 10:
            continue

        x_center = x + w / 2
        y_center = y + h / 2
        bounding_boxes.append((x, y, w, h, x_center, y_center, 0)) # x, y, w, h, x_center, y_center, is_merged

    merged_boxes = []
    for i, (x1, y1, w1, h1, xc1, yc1, _) in enumerate(bounding_boxes):
        merged = False
        for j, (x2, y2, w2, h2, xc2, yc2, _) in enumerate(merged_boxes):
            # 유클리드 거리 계산
            distance1 = np.sqrt((x1 - xc2) ** 2 + (y1 - yc2) ** 2)
            distance2 = np.sqrt((xc1 - xc2) ** 2 + (yc1 - yc2) ** 2)
            distance3 = np.sqrt((x1 + w1 - xc2) ** 2 + (y1 + h1 - yc2) ** 2)

            if distance1 <= merge_distance_threshold or distance2 <= merge_distance_threshold or distance3 <= merge_distance_threshold:
                # 병합된 바운딩 박스 계산
                new_x = min(x1, x2)
                new_y = min(y1, y2)
                new_w = max(x1 + w1, x2 + w2) - new_x
                new_h = max(y1 + h1, y2 + h2) - new_y
                # 1:1 비율로 조정
                max_side = max(new_w, new_h)
                new_w = max_side
                new_h = max_side
                merged_boxes[j] = (new_x, new_y, new_w, new_h, (new_x + new_w / 2), (new_y + new_h / 2), 1) # x, y, w, h, x_center, y_center, is_merged
                merged = True
                break

        if not merged:
            merged_boxes.append((x1, y1, w1, h1, xc1, yc1, 0)) # x, y, w, h, x_center, y_center, is_merged

    return merged_boxes

# 이미지 전처리 및 윤곽선 찾기
def preprocess_image_and_find_contours(img):
    # 그레이스케일로 변환
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 블러 적용
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # 이진화
    thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                    cv2.THRESH_BINARY_INV, 9, 2)

    # 윤곽선 찾기
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return contours


# prepare_image 함수는 주어진 이미지 경로에서 이미지를 읽고, 출력 디렉토리를 생성하는 역할을 합니다.
def prepare_image(image_path, output_dir):
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(image_path):
        print(f"Error: Image '{image_path}' does not exist")
        return None

    print(f'Processing {image_path}...')
    # 이미지 읽기
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image {image_path}")
        return None
    
    return img


def process_images_in_directory(horizontally_cropped_dir_path):
    # 상위 디렉토리 내의 answer와 question 디렉토리 순회
    for sub_dir in ['answer', 'question_number']:
        input_dir = os.path.join(horizontally_cropped_dir_path, sub_dir)
        
        # is_answer 설정
        is_answer = (sub_dir == 'answer')
        
        # output_dir 설정
        output_dir = os.path.join(horizontally_cropped_dir_path, '..', 'text_cropped', sub_dir)
        os.makedirs(output_dir, exist_ok=True)

        # 입력 디렉토리 내의 모든 이미지 파일에 대해 반복
        for root, dirs, files in os.walk(input_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                    image_path = os.path.join(root, file)
                    
                    # 이미지 읽기
                    img = cv2.imread(image_path)
                    if img is None:
                        print(f"Error: Could not read image {image_path}")
                        continue

                    # 이미지 전처리 및 윤곽선 찾기
                    contours = preprocess_image_and_find_contours(img)

                    # 병합 로직 적용
                    merged_boxes = merge_contours_v2(contours, output_dir=output_dir, img=img)

                    if merged_boxes:
                        img_output_dir = os.path.join(output_dir, f'{os.path.basename(image_path)}')
                        if not os.path.exists(img_output_dir):
                            os.makedirs(img_output_dir)

                        padding = 10  # 패딩 값 설정
                        for j, (x, y, w, h, xc, yc, is_merged) in enumerate(merged_boxes):
                            # 1:1 비율로 조정
                            max_side = max(w, h)
                            x_padded = max(x - padding, 0)
                            y_padded = max(y - padding, 0)
                            w_padded = min(w + 2 * padding, img.shape[1] - x_padded)
                            h_padded = min(h + 2 * padding, img.shape[0] - y_padded)

                            # 이미지 경계를 초과하지 않도록 조정
                            if x_padded + w_padded > img.shape[1]:
                                w_padded = img.shape[1] - x_padded
                            if y_padded + h_padded > img.shape[0]:
                                h_padded = img.shape[0] - y_padded

                            # 실제 이미지 크롭
                            cropped_img = img[y_padded:y_padded+h_padded, x_padded:x_padded+w_padded]
                            
                            # 1:1 비율로 만들기 위해 흰색 배경의 정사각형 이미지 생성
                            square_size = max(w_padded, h_padded)
                            square_img = np.ones((square_size, square_size, 3), dtype=np.uint8) * 255  # 흰색 배경
                            
                            # 원본 이미지를 정사각형 이미지의 중앙에 배치
                            offset_x = (square_size - w_padded) // 2
                            offset_y = (square_size - h_padded) // 2
                            square_img[offset_y:offset_y+h_padded, offset_x:offset_x+w_padded] = cropped_img
                            
                            # 최종 이미지 저장
                            base_name = os.path.basename(img_output_dir)
                            output_path = os.path.join(img_output_dir, f'{base_name}_x_{x}_is_merged_{is_merged}.jpg')
                            cv2.imwrite(output_path, square_img)
                            print(f'Saved {output_path}')
                        print(f'Saved {len(merged_boxes)} boxes from {image_path}')
                    else:
                        print(f'No boxes found in {image_path}')

if __name__ == '__main__':
    # 3. ready_for_ocr.text_crop_final: horizontally cropped 이미지 -> text crop 이미지
    horizontally_cropped_dir = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/horizontally_cropped'

    process_images_in_directory(horizontally_cropped_dir) 
