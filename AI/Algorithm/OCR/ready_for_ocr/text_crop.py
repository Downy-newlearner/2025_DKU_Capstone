'''
text_crop_one_image_v2.py 코드의 디버깅 버전
'''

import cv2
import numpy as np
import os

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
        bounding_boxes.append((x, y, w, h, x_center, y_center))

    # 모든 바운딩 박스를 원본 이미지 위에 그리기!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if img is not None and output_dir is not None:
        debug_img_all = img.copy()
        for (x, y, w, h, xc, yc) in bounding_boxes:
            cv2.rectangle(debug_img_all, (x, y), (x + w, y + h), (255, 255, 0), 1)  # 모든 바운딩 박스
        debug_output_path_all = os.path.join(output_dir, 'debug_all_bounding_boxes.jpg')
        cv2.imwrite(debug_output_path_all, debug_img_all)
    # 디버깅 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


    merged_boxes = []
    for i, (x1, y1, w1, h1, xc1, yc1) in enumerate(bounding_boxes):
        merged = False
        for j, (x2, y2, w2, h2, xc2, yc2) in enumerate(merged_boxes):
            # 유클리드 거리 계산
            distance1 = np.sqrt((x1 - xc2) ** 2 + (y1 - yc2) ** 2)
            distance2 = np.sqrt((xc1 - xc2) ** 2 + (yc1 - yc2) ** 2)
            distance3 = np.sqrt((x1 + w1 - xc2) ** 2 + (y1 + h1 - yc2) ** 2)

            print(f'i: {i}, j: {j}, distance1: {distance1}, distance2: {distance2}, distance3: {distance3}')
            if distance1 <= merge_distance_threshold or distance2 <= merge_distance_threshold or distance3 <= merge_distance_threshold:
                
                # 병합된 바운딩 박스 계산
                new_x = min(x1, x2)
                new_y = min(y1, y2)
                new_w = max(x1 + w1, x2 + w2) - new_x
                new_h = max(y1 + h1, y2 + h2) - new_y
                merged_boxes[j] = (new_x, new_y, new_w, new_h, (new_x + new_w / 2), (new_y + new_h / 2))
                merged = True

                # 병합 과정 시각화
                if img is not None and output_dir is not None:
                    debug_img = img.copy()
                    cv2.rectangle(debug_img, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 1)  # 기존 바운딩 박스
                    cv2.rectangle(debug_img, (x2, y2), (x2 + w2, y2 + h2), (255, 0, 0), 1)  # 병합 대상 바운딩 박스
                    cv2.rectangle(debug_img, (new_x, new_y), (new_x + new_w, new_y + new_h), (0, 0, 255), 2)  # 병합된 바운딩 박스
                    debug_output_path = os.path.join(output_dir, f'debug_merge_{i}_{j}.jpg')
                    cv2.imwrite(debug_output_path, debug_img)
                break

        if not merged:
            merged_boxes.append((x1, y1, w1, h1, xc1, yc1))

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



def process_single_image_v2(image_path, output_dir, is_answer):
    # 이미지 준비
    img = prepare_image(image_path, output_dir)
    if img is None:
        return

    # 이미지 전처리 및 윤곽선 찾기
    contours = preprocess_image_and_find_contours(img)

    # 병합 로직 적용
    merged_boxes = merge_contours_v2(contours, output_dir=output_dir, img=img)

    if merged_boxes:
        img_output_dir = os.path.join(output_dir, f'{"answer" if is_answer else "question"}_{os.path.basename(image_path)}')
        if not os.path.exists(img_output_dir):
            os.makedirs(img_output_dir)
        
        for j, (x, y, w, h, xc, yc) in enumerate(merged_boxes):
            # 실제 이미지 크롭
            cropped_img = img[y:y+h, x:x+w]
            output_path = os.path.join(img_output_dir, f'box_{j+1}_{x}_{y}_{w}_{h}.jpg')
            cv2.imwrite(output_path, cropped_img)
        print(f'Saved {len(merged_boxes)} boxes from {image_path}')
    else:
        print(f'No boxes found in {image_path}')

if __name__ == '__main__':
    process_single_image_v2(
        image_path='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/cropped_images_question_number/question_4_295_407.jpg',
        output_dir='../cropped_data/question_4_295_407',
        is_answer=False
    )
