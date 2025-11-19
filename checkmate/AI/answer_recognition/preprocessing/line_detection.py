'''
written by 오유석 0410
editted by 정다훈 0411

--- note by 정다훈 0411
수정한 'detect_and_crop_by_line' 함수 설명은 아래와 같다.

1. 파라미터 
    - image_path
    - output_dir
    - is_answer
        question_number 이미지면 False, answer 이미지면 True로 입력하면 된다.
        이 파라미터에 따라 저장 파일명이 달라진다.



0514 수정 사항 by 정다훈:
- image_path 대신 image_dir_path를 받아 os.walk로 디렉토리를 순회하며 이미지 파일을 처리하도록 변경
- 이미지 파일명에 따라 is_answer 값을 설정하도록 변경
'''

import cv2
import numpy as np
import os

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

def enhance_horizontal_lines(image):
    # 그레이스케일로 변환
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 대비 향상
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    
    # 노이즈 제거를 위한 블러
    blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
    
    # Otsu's 이진화로 자동 임계값 설정
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # 수평선 강화
    horizontal_size = image.shape[1] // 2
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)
    
    return horizontal_lines

def detect_and_crop_by_lines(image_dir_path, output_dir):
    # image_dir_path 경로 순회
    for root, dirs, files in os.walk(image_dir_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpeg', '.jpg')):
                image_path = os.path.join(root, file)
                
                # 파일명에 따라 is_answer 결정
                if 'answer' in file.lower():
                    is_answer = True
                elif 'question_number' in file.lower():
                    is_answer = False
                else:
                    continue  # 파일명이 조건에 맞지 않으면 건너뜀

                # 이미지 읽기
                image = cv2.imread(image_path)
                if image is None:
                    print(f"Error: Could not read image at {image_path}")
                    continue

                # 수평선 강화
                horizontal_lines = enhance_horizontal_lines(image)

                # 윤곽선 검출
                contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # 디버그 by 다훈 0411
            # print(contours)
            
            # 감지된 선들의 y 좌표를 저장
            y_coordinates = []
            min_line_width = image.shape[1] // 5  # 최소 선 길이 완화
            
            print("이제 contour들을 출력함")
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w >= min_line_width and h <= 10:  # 수평선으로 간주할 수 있는 윤곽선 필터링
                    # 선의 중심점 대신 상단과 하단 모두 저장
                    y_coordinates.extend([y, y + h])
            
            # 이미지 상단과 하단 추가
            y_coordinates.append(0)
            y_coordinates.append(image.shape[0])
            
            # y 좌표 정렬 및 중복 제거
            y_coordinates = sorted(list(set(y_coordinates)))

            # 디버깅 by 다훈 0411
            print(y_coordinates)
            
            # 너무 가까운 좌표 병합
            merged_y = []
            i = 0
            while i < len(y_coordinates):
                current = y_coordinates[i]
                j = i + 1
                while j < len(y_coordinates) and y_coordinates[j] - current < 15:
                    j += 1
                merged_y.append(current)
                i = j
            
            y_coordinates = merged_y


            # !!!! 여기부터 output 디렉토리 생성 및 이미지 저장 코드 !!!!
            if is_answer:
                output_dir_final = os.path.join(output_dir, 'answer')
            else:
                output_dir_final = os.path.join(output_dir, 'question')
            
            # 출력 디렉토리 생성
            os.makedirs(output_dir_final, exist_ok=True)
            
            # 각 선 사이의 영역을 크롭
            for i in range(len(y_coordinates) - 1):
                y_start = y_coordinates[i]
                y_end = y_coordinates[i + 1]
                
                # 너무 작은 영역만 건너뛰기 (최대 높이 제한 제거)
                height = y_end - y_start
                if height < 20:  # 최소 높이만 체크
                    continue
                
                # 이미지 크롭
                cropped = image[y_start:y_end, 0:image.shape[1]]
                
                # 크롭된 이미지 저장
                if(is_answer):
                    output_path = os.path.join(output_dir_final, f'answer_{i+1}_{y_start}_{y_end}.jpg')
                else:    
                    output_path = os.path.join(output_dir_final, f'question_{i+1}_{y_start}_{y_end}.jpg')
                    # 여기까지 파일명에 크롭된 이미지의 원래 y_top, y_bottom 작성 완료 ㅋㅋ by 다훈 0411
                cv2.imwrite(output_path, cropped)
                print(f"Saved cropped image to {output_path}")
            
            print(f"Total number of images created: {len(os.listdir(output_dir_final))}")

def main():
    # 이미지 경로와 출력 디렉토리 설정
    image_dir_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/yolov10/test_splitted'
    output_dir = 'cropped_images'
    
    # 기존 출력 디렉토리 내용 삭제
    if os.path.exists(output_dir):
        for file in os.listdir(output_dir):
            file_path = os.path.join(output_dir, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

    detect_and_crop_by_lines(image_dir_path, output_dir)

if __name__ == "__main__":
    main() 