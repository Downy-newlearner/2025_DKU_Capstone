# 여기에 패들 코드, yolo 코드를 통합하여 extract_student_num 함수 작성

import subprocess
from pathlib import Path
import cv2
import numpy as np
from paddleocr import PaddleOCR
import os
import json
from datetime import datetime
import shutil
import traceback
import base64


'''
- 함수 이름: extract_student_num

- Param: `answer_sheet_img_path` → str
    - `answer_sheet_img_path`: 답안지 이미지 경로

- Return: `student_num` → int | None
    - 추출된 학번 (8자리 정수)
    - 인식 실패시 None 반환

- Logic:
    1. YOLO로 학번 영역 검출
    2. 검출된 영역 이미지 크롭
    3. OCR로 숫자 인식
    4. 가장 높은 신뢰도를 가진 숫자 반환
'''
def extract_student_num(answer_sheet_img_path: str) -> int | None:
    """
    답안지 이미지에서 학번을 추출하는 함수
    
    Args:
        answer_sheet_img_path (str): 답안지 이미지 경로
    
    Returns:
        int | None: 추출된 학번 (8자리 정수), 인식 실패시 None
    """
    try:
        # YOLO 결과를 저장할 임시 디렉토리 설정
        temp_dir = os.path.join(os.path.dirname(__file__), "results", "temp_detection")
        
        # 이전 결과 정리
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        # 1. YOLO를 통한 학번 영역 검출
        # YOLO 명령어 구성 및 실행
        command = [
            "yolo",
            "predict",
            f"model={os.path.join(os.path.dirname(__file__), 'student_number_best.pt')}",
            f"source={answer_sheet_img_path}",
            f"project={os.path.join(os.path.dirname(__file__), 'results')}",
            f"name=temp_detection",
            "save_txt=true"
        ]
        
        print(f"실행 명령어: {' '.join(command)}")
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"YOLO detection failed for {os.path.basename(answer_sheet_img_path)}")
            return None, ""
            
        # 2. 라벨 파일 경로 설정
        image_name = Path(answer_sheet_img_path).stem
        label_path = Path(os.path.join(temp_dir, "labels")) / f"{image_name}.txt"
        
        if not label_path.exists():
            print(f"Label file not found for {os.path.basename(answer_sheet_img_path)}")
            return None, ""
        
        # 3. 이미지 크롭
        # 이미지 읽기
        image = cv2.imread(answer_sheet_img_path)
        if image is None:
            print(f"Could not read image: {os.path.basename(answer_sheet_img_path)}")
            return None, ""
        
        height, width = image.shape[:2]
        
        # bbox 좌표 읽기
        with open(label_path, 'r') as f:
            line = f.readline().strip().split()
            if len(line) >= 5:  # class_id, center_x, center_y, width, height
                center_x, center_y, w, h = map(float, line[1:5])
            else:
                print(f"Invalid label format for {os.path.basename(answer_sheet_img_path)}")
                return None, ""
        
        # 정규화된 좌표를 실제 픽셀 좌표로 변환
        x1 = int((center_x - w/2) * width)
        y1 = int((center_y - h/2) * height)
        x2 = int((center_x + w/2) * width)
        y2 = int((center_y + h/2) * height)
        
        # 좌표가 이미지 범위를 벗어나지 않도록 조정
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        # 이미지 자르기
        cropped_image = image[y1:y2, x1:x2]
        
        # 이미지를 base64로 변환
        # NumPy 배열을 연속적인 메모리로 만들고, JPEG로 인코딩
        _, buffer = cv2.imencode('.jpg', cropped_image)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 4. OCR로 학번 인식
        ocr = PaddleOCR(use_angle_cls=True, lang='en')
        result = ocr.ocr(cropped_image, cls=True)
        
        if not result:
            print(f"No text detected by OCR for {os.path.basename(answer_sheet_img_path)}")
            return None, img_base64
            
        # OCR 결과에서 가장 높은 신뢰도를 가진 숫자 찾기
        best_number = None
        best_confidence = 0
        
        for line_ocr_result in result:
            if line_ocr_result is None:
                continue

            for word_info in line_ocr_result:
                # PaddleOCR v2.6 이상에서 word_info는 [bbox, (text, score)] 형태일 수 있음
                # word_info[0]은 bbox 좌표 리스트
                # word_info[1]은 (인식된 텍스트, 신뢰도 점수) 튜플
                if len(word_info) >= 2 and isinstance(word_info[1], tuple) and len(word_info[1]) >= 2:
                    text = word_info[1][0]
                    confidence = float(word_info[1][1])
                else:
                    # 예상치 못한 형식의 word_info는 건너뜀
                    # print(f"Unexpected word_info format: {word_info} for {os.path.basename(answer_sheet_img_path)}")
                    continue
                
                # 숫자만 추출
                numbers = ''.join(filter(str.isdigit, text))
                
                if numbers and confidence > best_confidence:
                    try:
                        number_int = int(numbers)
                        best_number = number_int
                        best_confidence = confidence
                    except ValueError:
                        continue
        
        if best_number is not None:
            print(f"Found student ID: {best_number} for {os.path.basename(answer_sheet_img_path)}")
            return best_number, img_base64
        else:
            print(f"No valid student number found for {os.path.basename(answer_sheet_img_path)}")
            return None, img_base64
            
    except Exception as e:
        print(f"Error processing {os.path.basename(answer_sheet_img_path)}: {str(e)}")
        print("--- Full Traceback ---")
        traceback.print_exc()
        print("--- End Traceback ---")
        return None, img_base64


if __name__ == "__main__":
    # 테스트용 디렉토리 경로
    test_dir = "/Users/ohyooseok/AI/Student_id_recognition/decompression_parsing/test_answer"
    
    # 결과를 저장할 딕셔너리
    results_summary = {
        "test_time": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "results": []
    }
    
    try:
        # 디렉토리 내의 모든 jpg 파일 처리
        for img_file in os.listdir(test_dir):
            if img_file.endswith('.jpg'):
                img_path = os.path.join(test_dir, img_file)
                print(f"\nProcessing image: {img_file}")
                student_num, img_base64 = extract_student_num(img_path)
                
                # 결과 저장
                result_entry = {
                    "image_file": img_file,
                    "student_number": student_num,
                    "success": student_num is not None,
                    "cropped_image_base64": img_base64  # base64 이미지 데이터 추가
                }
                results_summary["results"].append(result_entry)
                
                print(f"Result for {img_file}: {student_num}")
                print("-" * 50)
    finally:
        # 임시 폴더 정리
        temp_detection_dir = os.path.join(os.path.dirname(__file__), "results", "temp_detection")
        if os.path.exists(temp_detection_dir):
            shutil.rmtree(temp_detection_dir)
            print("\nCleaned up temporary directory")
    
    # 결과를 JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    result_file_path = os.path.join(os.path.dirname(__file__), f"test_results_{timestamp}.json")
    
    with open(result_file_path, 'w', encoding='utf-8') as f:
        json.dump(results_summary, f, ensure_ascii=False, indent=2)
    
    print(f"\nTest results saved to: {result_file_path}")
    
    # 성공/실패 통계 출력
    if results_summary["results"]:
        total = len(results_summary["results"])
        successful = sum(1 for r in results_summary["results"] if r["success"])
        print(f"\nProcessing Statistics:")
        print(f"Total images: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        if total > 0:
            print(f"Success rate: {(successful/total)*100:.2f}%")
    else:
        print("\nNo images processed or found.")