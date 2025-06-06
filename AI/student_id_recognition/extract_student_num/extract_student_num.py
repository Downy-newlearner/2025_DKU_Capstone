# student_id_recognition/extract_student_num/extract_student_num.py
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
from typing import Union, Tuple

# INTER_LINEAR이 없으면 대체값 직접 설정 (보통 1)
if not hasattr(cv2, 'INTER_LINEAR'):
    cv2.INTER_LINEAR = 1

def extract_student_num(answer_sheet_img_path: str) -> Tuple[Union[int, None], str]:
    """
    답안지 이미지에서 학번을 추출하고 크롭된 학번 영역의 Base64를 반환합니다.
    
    Args:
        answer_sheet_img_path (str): 답안지 이미지 경로
    
    Returns:
        tuple[int | None, str]: (추출된 학번, 학번 영역 이미지의 Base64 문자열).
                                학번 인식 실패 시 (None, 해당 시점까지 생성된 Base64 문자열).
                                Base64 생성 실패 또는 오류 발생 시 (학번 또는 None, "").
    """
    img_base64 = "" # 예외 발생 또는 조기 반환 시 기본값
    try:
        # YOLO 결과를 저장할 임시 디렉토리 설정
        temp_dir = os.path.join(os.path.dirname(__file__), "results", "temp_detection")
        
        # 이전 결과 정리
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        # 1. YOLO를 통한 학번 영역 검출
        command = [
            "yolo",
            "predict",
            f"model={os.path.join(os.path.dirname(__file__), 'student_number_best.pt')}",
            f"source={answer_sheet_img_path}",
            f"project={os.path.join(os.path.dirname(__file__), 'results')}",
            f"name=temp_detection",
            "save_txt=true"
        ]
        
        process_result = subprocess.run(command, capture_output=True, text=True)
        
        if process_result.returncode != 0:
            print(f"YOLO detection failed for {os.path.basename(answer_sheet_img_path)}: {process_result.stderr}")
            return None, ""
            
            
        # 2. 라벨 파일 경로 설정
        image_name = Path(answer_sheet_img_path).stem
        label_path = Path(os.path.join(temp_dir, "labels")) / f"{image_name}.txt"
        
        if not label_path.exists():
            print(f"Label file not found for {os.path.basename(answer_sheet_img_path)}")
            return None, ""
        
        # 3. 이미지 크롭
        image = cv2.imread(answer_sheet_img_path)
        if image is None:
            print(f"Could not read image: {os.path.basename(answer_sheet_img_path)}")
            return None, ""
        
        height, width = image.shape[:2]
        
        with open(label_path, 'r') as f:
            line = f.readline().strip().split()
            if len(line) >= 5:
                center_x, center_y, w, h = map(float, line[1:5])
            else:
                print(f"Invalid label format for {os.path.basename(answer_sheet_img_path)}")
                return None, ""
        
        x1 = int((center_x - w/2) * width)
        y1 = int((center_y - h/2) * height)
        x2 = int((center_x + w/2) * width)
        y2 = int((center_y + h/2) * height)
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(width, x2)
        y2 = min(height, y2)
        
        cropped_image = image[y1:y2, x1:x2]
        
        # 디버깅: 크롭된 이미지 저장
        try:
            debug_crop_dir = os.path.join(os.path.dirname(__file__), "results", "debug_cropped_images")
            if not os.path.exists(debug_crop_dir):
                os.makedirs(debug_crop_dir)
            
            original_image_name = Path(answer_sheet_img_path).stem
            debug_crop_filename = f"debug_crop_{original_image_name}.jpg"
            debug_crop_path = os.path.join(debug_crop_dir, debug_crop_filename)

            if cropped_image is not None and cropped_image.size > 0:
                cv2.imwrite(debug_crop_path, cropped_image)
                print(f"DEBUG: Saved cropped image to {debug_crop_path}")
            else:
                print(f"DEBUG: Cropped image for {original_image_name} is empty, not saving.")
        except Exception as debug_save_e:
            print(f"DEBUG: Error saving cropped image for {original_image_name}: {str(debug_save_e)}")

        # 디버깅: 크롭된 이미지 상태 확인
        if cropped_image is None or cropped_image.size == 0:
            print(f"DEBUG: Cropped image is empty or invalid for {os.path.basename(answer_sheet_img_path)}. Shape: {cropped_image.shape if cropped_image is not None else 'None'}")
            img_base64 = "" # 빈 이미지에 대한 Base64는 빈 문자열로 설정
        else:
            print(f"DEBUG: Cropped image shape for {os.path.basename(answer_sheet_img_path)}: {cropped_image.shape}")
            # 이미지를 base64로 변환
            retval, buffer = cv2.imencode('.jpg', cropped_image)
            if retval and buffer is not None:
                print(f"DEBUG: cv2.imencode success. Buffer length: {len(buffer)} for {os.path.basename(answer_sheet_img_path)}")
                img_base64 = base64.b64encode(buffer).decode('utf-8')
            else:
                print(f"DEBUG: cv2.imencode failed or returned empty buffer for {os.path.basename(answer_sheet_img_path)}. retval: {retval}")
                img_base64 = "" # 인코딩 실패 시 빈 문자열
        
        # 4. OCR로 학번 인식
        ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False) # show_log=False 추가하여 PaddleOCR 로그 줄임
        ocr_result = ocr.ocr(cropped_image, cls=True)
        
        if not ocr_result or not ocr_result[0]: # OCR 결과가 비었거나, 첫 번째 라인이 없는 경우
            print(f"No text detected by OCR for {os.path.basename(answer_sheet_img_path)}")
            return None, img_base64
            
        best_number = None
        best_confidence = 0
        
        for line_ocr_result in ocr_result:
            if line_ocr_result is None:
                continue

            for word_info in line_ocr_result:
                if len(word_info) >= 2 and isinstance(word_info[1], tuple) and len(word_info[1]) >= 2:
                    text = word_info[1][0]
                    confidence = float(word_info[1][1])
                else:
                    continue
                
                numbers = ''.join(filter(str.isdigit, text))
                
                if numbers and confidence > best_confidence:
                    try:
                        number_int = int(numbers)
                        best_number = number_int
                        best_confidence = confidence
                    except ValueError:
                        continue
        
        if best_number is not None:
            # print(f"Found student ID: {best_number} for {os.path.basename(answer_sheet_img_path)}") # 로그 레벨 조정을 위해 주석 처리 가능
            return best_number, img_base64
        else:
            # print(f"No valid student number found for {os.path.basename(answer_sheet_img_path)}") # 로그 레벨 조정을 위해 주석 처리 가능
            return None, img_base64
            
    except Exception as e:
        print(f"Error processing {os.path.basename(answer_sheet_img_path)}: {str(e)}")
        print("--- Full Traceback ---")
        traceback.print_exc()
        print("--- End Traceback ---")
        if 'img_base64' not in locals(): # 예외 발생 시 img_base64가 정의되지 않았을 수 있음
            img_base64 = ""
        return None, img_base64


if __name__ == "__main__":
    # 테스트용 디렉토리 경로
    test_dir = "/home/jdh251425/2025_DKU_Capstone/AI/student_id_recognition/extract_student_num/test_answer" # 실제 경로로 수정 필요
    
    # 결과를 저장할 딕셔너리
    results_summary = {
        "test_time": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "results": []
    }
    
    try:
        # 디렉토리 내의 모든 지원 이미지 파일 처리
        for img_file in os.listdir(test_dir):
            if img_file.lower().endswith(('.jpg', '.jpeg', '.png')): # 다양한 이미지 확장자 지원
                img_path = os.path.join(test_dir, img_file)
                print(f"\nProcessing image: {img_file}")
                student_num, current_img_base64 = extract_student_num(img_path)
                
                # 결과 저장
                result_entry = {
                    "image_file": img_file,
                    "student_number": student_num,
                    "success": student_num is not None,
                    "cropped_image_base64": current_img_base64 
                }
                results_summary["results"].append(result_entry)
                
                print(f"Result for {img_file}: StudentNum={student_num}, Base64Length={len(current_img_base64) if current_img_base64 else 0}")
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
