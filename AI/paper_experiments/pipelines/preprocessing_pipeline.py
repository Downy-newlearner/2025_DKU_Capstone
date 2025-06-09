"""
3단계 전처리 파이프라인 + MNIST 분류 모델 실험 모듈

단계:
1. 절반 크롭: YOLO로 답안 영역 추출 (이미 완료 - yolo_answer_images 사용)
2. 수평 크롭: 수평선 기준으로 행 분할
3. 텍스트 크롭: 개별 숫자 블록 분할
4. 단일 숫자 인식: MNIST 기반 Vision Transformer
"""

import cv2
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image, ImageDraw
from transformers import pipeline
import sys
import os

# answer_recognition 모듈의 경로를 sys.path에 추가
answer_recognition_path = Path(__file__).parent.parent / "answer_recognition"
sys.path.append(str(answer_recognition_path))

from config import (
    YOLO_ANSWER_IMAGES_DIR, RESULTS_DIR, VISUALIZATION_DIR,
    BBOX_COLOR, BBOX_THICKNESS, TEXT_COLOR, TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS
)

# MNIST 모델 초기화
try:
    mnist_model = pipeline("image-classification", 
                          model="farleyknight/mnist-digit-classification-2022-09-04", 
                          device=-1)  # CPU 사용
    print("✅ MNIST 분류 모델 로드 완료")
except Exception as e:
    print(f"❌ MNIST 분류 모델 로드 실패: {e}")
    mnist_model = None

# 결과 저장 디렉토리
PIPELINE_RESULTS_DIR = RESULTS_DIR / "pipeline_results"
PIPELINE_VISUALIZATION_DIR = RESULTS_DIR / "pipeline_visualizations"


class PreprocessingPipeline:
    """3단계 전처리 파이프라인 클래스"""
    
    def __init__(self):
        """파이프라인 초기화"""
        self.mnist_model = mnist_model
        
        # 출력 디렉토리 생성
        PIPELINE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        PIPELINE_VISUALIZATION_DIR.mkdir(parents=True, exist_ok=True)
    
    def step2_horizontal_crop(self, answer_image: Image.Image) -> List[Dict[str, Any]]:
        """
        2단계: 수평 크롭 - 수평선 기준으로 행 분할
        
        Args:
            answer_image: YOLO로 추출된 답안 이미지
            
        Returns:
            라인별 이미지와 위치 정보 리스트
        """
        print("    🔄 2단계: 수평선 검출 및 행 분할")
        
        # PIL을 OpenCV로 변환
        cv_image = cv2.cvtColor(np.array(answer_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 수평선 검출을 위한 전처리
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
        
        # 수평 커널을 사용한 형태학적 연산
        horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
        horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 수평선 정보 추출
        line_info = []
        min_width = answer_image.width * 0.2  # 최소 선 길이
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > min_width:  # 충분히 긴 선만 선택
                line_info.append({'y': y, 'height': h})
        
        # y 좌표 기준 정렬
        line_info.sort(key=lambda x: x['y'])
        
        # 가까운 선들 병합
        merged_lines = []
        for line in line_info:
            if not merged_lines or line['y'] - merged_lines[-1]['y'] > 15:
                merged_lines.append(line)
        
        print(f"      🔍 {len(merged_lines)}개의 수평선 검출됨")
        
        # 라인 간 영역 분할
        line_crops = []
        image_height = answer_image.height
        
        for i in range(len(merged_lines) + 1):
            if i == 0:
                # 첫 번째 라인 위쪽
                y_start = 0
                y_end = merged_lines[0]['y'] if merged_lines else image_height
            elif i == len(merged_lines):
                # 마지막 라인 아래쪽
                y_start = merged_lines[-1]['y'] + merged_lines[-1]['height']
                y_end = image_height
            else:
                # 라인 사이 영역
                y_start = merged_lines[i-1]['y'] + merged_lines[i-1]['height']
                y_end = merged_lines[i]['y']
            
            # 유효한 높이인지 확인
            if y_end - y_start > 20:  # 최소 높이
                line_crop = answer_image.crop((0, y_start, answer_image.width, y_end))
                line_crops.append({
                    'image': line_crop,
                    'y_start': y_start,
                    'y_end': y_end,
                    'line_index': len(line_crops)
                })
        
        print(f"      ✅ {len(line_crops)}개의 행으로 분할 완료")
        return line_crops
    
    def step3_text_crop(self, line_image: Image.Image, y_offset: int) -> List[Dict[str, Any]]:
        """
        3단계: 텍스트 크롭 - 개별 숫자 블록 분할
        
        Args:
            line_image: 행별 이미지
            y_offset: 원본 이미지에서의 y 오프셋
            
        Returns:
            텍스트 블록별 이미지와 위치 정보 리스트
        """
        # PIL을 OpenCV로 변환
        cv_image = cv2.cvtColor(np.array(line_image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 이진화
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 윤곽선 검출
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 바운딩 박스 추출 및 필터링
        bboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > 5 and h > 5:  # 최소 크기 필터링
                bboxes.append((x, y, w, h))
        
        # x 좌표 기준 정렬
        bboxes.sort(key=lambda box: box[0])
        
        # 가까운 박스들 병합
        merged_bboxes = []
        merge_distance = 50
        
        for bbox in bboxes:
            x, y, w, h = bbox
            
            # 기존 박스와 병합 가능한지 확인
            merged = False
            for i, (mx, my, mw, mh) in enumerate(merged_bboxes):
                if abs(x - (mx + mw)) < merge_distance:  # 가까운 거리
                    # 병합
                    new_x = min(x, mx)
                    new_y = min(y, my)
                    new_w = max(x + w, mx + mw) - new_x
                    new_h = max(y + h, my + mh) - new_y
                    merged_bboxes[i] = (new_x, new_y, new_w, new_h)
                    merged = True
                    break
            
            if not merged:
                merged_bboxes.append(bbox)
        
        # 텍스트 블록 추출
        text_crops = []
        for i, (x, y, w, h) in enumerate(merged_bboxes):
            # 여백 추가
            padding = 5
            crop_x = max(0, x - padding)
            crop_y = max(0, y - padding)
            crop_w = min(line_image.width - crop_x, w + 2 * padding)
            crop_h = min(line_image.height - crop_y, h + 2 * padding)
            
            text_crop = line_image.crop((crop_x, crop_y, crop_x + crop_w, crop_y + crop_h))
            
            text_crops.append({
                'image': text_crop,
                'x_in_line': crop_x,
                'y_in_line': crop_y,
                'width': crop_w,
                'height': crop_h,
                'x_in_answer': crop_x,  # 답안 이미지 기준 x좌표
                'y_in_answer': y_offset + crop_y,  # 답안 이미지 기준 y좌표
                'text_index': i
            })
        
        return text_crops
    
    def step4_digit_recognition(self, text_image: Image.Image) -> List[Dict[str, Any]]:
        """
        4단계: 단일 숫자 인식 - MNIST 기반 분류
        
        Args:
            text_image: 텍스트 블록 이미지
            
        Returns:
            인식된 숫자들과 위치 정보 리스트
        """
        if not self.mnist_model:
            return []
        
        # PIL을 OpenCV로 변환하여 윤곽선 검출
        cv_image = cv2.cvtColor(np.array(text_image.convert('L')), cv2.COLOR_GRAY2BGR)
        gray = cv2.cvtColor(cv_image, cv2.COLOR_BGR2GRAY)
        
        # 이진화
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # 개별 숫자 윤곽선 검출
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        digit_results = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # 크기 필터링
            if w < 5 or h < 5:
                continue
            
            # 개별 숫자 이미지 추출
            digit_image = text_image.convert('L').crop((x, y, x + w, y + h))
            
            # 28x28로 리사이즈 (MNIST 형식)
            digit_image = digit_image.resize((28, 28), Image.Resampling.LANCZOS)
            
            try:
                # MNIST 모델로 예측
                prediction = self.mnist_model(digit_image)
                if prediction and len(prediction) > 0:
                    predicted_digit = prediction[0]['label']
                    confidence = prediction[0]['score']
                    
                    digit_results.append({
                        'digit': predicted_digit,
                        'confidence': confidence,
                        'bbox': (x, y, w, h),
                        'x_center': x + w // 2,
                        'y_center': y + h // 2
                    })
            except Exception as e:
                print(f"        ⚠️ 숫자 인식 실패: {e}")
                continue
        
        # x 좌표 기준 정렬
        digit_results.sort(key=lambda d: d['x_center'])
        
        return digit_results
    
    def process_single_answer_image(self, image_path: Path) -> Dict[str, Any]:
        """
        단일 답안 이미지에 대해 전체 파이프라인 실행
        
        Args:
            image_path: YOLO로 추출된 답안 이미지 경로
            
        Returns:
            처리 결과 딕셔너리
        """
        start_time = time.time()
        
        try:
            # 답안 이미지 로드
            answer_image = Image.open(image_path).convert('RGB')
            
            print(f"  📖 전처리 파이프라인 시작: {image_path.name}")
            print(f"    📏 답안 이미지 크기: {answer_image.size}")
            
            # 2단계: 수평 크롭
            line_crops = self.step2_horizontal_crop(answer_image)
            
            # 3-4단계: 각 행에 대해 텍스트 크롭 및 숫자 인식
            all_text_crops = []
            all_digit_results = []
            
            for line_data in line_crops:
                print(f"      🔄 3단계: 행 {line_data['line_index']} 텍스트 크롭")
                
                text_crops = self.step3_text_crop(line_data['image'], line_data['y_start'])
                print(f"        📦 {len(text_crops)}개의 텍스트 블록 검출")
                
                for text_data in text_crops:
                    print(f"          🔄 4단계: 텍스트 블록 {text_data['text_index']} 숫자 인식")
                    
                    digit_results = self.step4_digit_recognition(text_data['image'])
                    
                    # 좌표 보정 (답안 이미지 기준)
                    for digit in digit_results:
                        digit['x_in_answer'] = text_data['x_in_answer'] + digit['bbox'][0]
                        digit['y_in_answer'] = text_data['y_in_answer'] + digit['bbox'][1]
                    
                    # 결과 저장
                    text_result = {
                        'text_crop_info': text_data,
                        'digit_results': digit_results,
                        'line_index': line_data['line_index']
                    }
                    
                    all_text_crops.append(text_result)
                    all_digit_results.extend(digit_results)
                    
                    print(f"            ✅ {len(digit_results)}개 숫자 인식: " + 
                          " ".join([d['digit'] for d in digit_results]))
            
            processing_time = time.time() - start_time
            
            # 전체 결과 조합 (왼쪽→오른쪽 순서)
            all_digit_results.sort(key=lambda d: (d['y_in_answer'], d['x_in_answer']))
            final_result = "".join([d['digit'] for d in all_digit_results 
                                  if d['confidence'] > 0.7])
            
            print(f"    ✅ 파이프라인 완료: '{final_result}' (처리시간: {processing_time:.2f}초)")
            
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "processing_time": processing_time,
                "line_crops": len(line_crops),
                "text_crops": len(all_text_crops),
                "total_digits": len(all_digit_results),
                "final_result": final_result,
                "digit_details": all_digit_results,
                "text_crop_details": all_text_crops,
                "success": True
            }
            
        except Exception as e:
            print(f"    ❌ 파이프라인 실패: {e}")
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "error": str(e),
                "success": False
            }
    
    def visualize_pipeline_results(self, image_path: Path, result: Dict[str, Any]) -> Optional[Path]:
        """
        파이프라인 결과를 답안 이미지에 시각화
        
        Args:
            image_path: 원본 답안 이미지 경로
            result: 파이프라인 결과
            
        Returns:
            시각화된 이미지 저장 경로
        """
        try:
            # 답안 이미지 로드
            answer_image = cv2.imread(str(image_path))
            if answer_image is None:
                return None
            
            vis_image = answer_image.copy()
            
            if result.get("success", False) and result.get("digit_details", []):
                # 각 인식된 숫자에 대해 바운딩 박스와 결과 표시
                for digit in result["digit_details"]:
                    x = digit['x_in_answer']
                    y = digit['y_in_answer']
                    w, h = digit['bbox'][2], digit['bbox'][3]
                    
                    # 바운딩 박스 그리기 (초록색)
                    cv2.rectangle(vis_image, (x, y), (x + w, y + h), BBOX_COLOR, BBOX_THICKNESS)
                    
                    # 인식 결과와 신뢰도 표시
                    label = f"{digit['digit']} ({digit['confidence']:.2f})"
                    
                    # 텍스트 배경
                    (text_width, text_height), baseline = cv2.getTextSize(
                        label, TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS
                    )
                    
                    cv2.rectangle(
                        vis_image,
                        (x, y - text_height - baseline - 5),
                        (x + text_width, y),
                        (0, 0, 0),
                        -1
                    )
                    
                    # 텍스트 그리기
                    cv2.putText(
                        vis_image,
                        label,
                        (x, y - baseline - 2),
                        TEXT_FONT,
                        TEXT_SCALE,
                        TEXT_COLOR,
                        TEXT_THICKNESS
                    )
            
            # 하단에 결과 요약 정보 표시
            info_lines = [
                f"Pipeline Result: {result.get('final_result', 'N/A')}",
                f"Digits: {result.get('total_digits', 0)}, Time: {result.get('processing_time', 0):.2f}s"
            ]
            
            y_pos = vis_image.shape[0] - 40
            for line in info_lines:
                cv2.putText(
                    vis_image,
                    line,
                    (10, y_pos),
                    TEXT_FONT,
                    TEXT_SCALE,
                    (255, 255, 255),  # 흰색
                    TEXT_THICKNESS
                )
                y_pos += 25
            
            # 저장
            output_path = PIPELINE_VISUALIZATION_DIR / f"{image_path.stem}_pipeline_vis.jpg"
            cv2.imwrite(str(output_path), vis_image)
            
            return output_path
            
        except Exception as e:
            print(f"❌ 시각화 실패: {e}")
            return None
    
    def run_pipeline_experiment(self, input_dir: Path = None) -> List[Dict[str, Any]]:
        """
        모든 답안 이미지에 대해 파이프라인 실험 실행
        
        Args:
            input_dir: 입력 디렉토리 (기본값: YOLO_ANSWER_IMAGES_DIR)
            
        Returns:
            모든 이미지의 파이프라인 결과 리스트
        """
        input_dir = input_dir or YOLO_ANSWER_IMAGES_DIR
        
        if not input_dir.exists():
            print(f"❌ 입력 디렉토리가 존재하지 않습니다: {input_dir}")
            return []
        
        # 답안 이미지 파일 찾기
        image_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.png"))
        
        if not image_files:
            print(f"❌ 답안 이미지 파일을 찾을 수 없습니다: {input_dir}")
            return []
        
        print(f"📁 총 {len(image_files)}개의 답안 이미지 발견")
        print("=" * 60)
        print("3단계 전처리 파이프라인 + MNIST 분류 실험 시작")
        print("=" * 60)
        
        all_results = []
        total_processing_time = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 처리 중: {image_path.name}")
            
            # 파이프라인 실행
            result = self.process_single_answer_image(image_path)
            all_results.append(result)
            
            if result.get("success", False):
                processing_time = result.get("processing_time", 0)
                total_processing_time += processing_time
                
                # 시각화
                vis_path = self.visualize_pipeline_results(image_path, result)
                if vis_path:
                    print(f"  🎨 시각화 저장: {vis_path.name}")
                
            else:
                error_msg = result.get("error", "알 수 없는 오류")
                print(f"  ❌ 파이프라인 실패: {error_msg}")
        
        # 전체 결과 요약
        print("\n" + "=" * 60)
        print("3단계 전처리 파이프라인 + MNIST 분류 실험 완료")
        print("=" * 60)
        
        successful_results = [r for r in all_results if r.get("success", False)]
        total_digits = sum(r.get("total_digits", 0) for r in successful_results)
        avg_processing_time = total_processing_time / len(successful_results) if successful_results else 0
        
        print(f"✅ 성공한 이미지: {len(successful_results)}/{len(image_files)}")
        print(f"🎯 총 인식 숫자: {total_digits}")
        print(f"⏱️  평균 처리 시간: {avg_processing_time:.2f}초")
        print(f"📂 시각화 결과: {PIPELINE_VISUALIZATION_DIR}")
        
        # 결과를 JSON 파일로 저장
        result_file = PIPELINE_RESULTS_DIR / "pipeline_results.json"
        
        def json_serializer(obj):
            """NumPy 데이터 타입을 JSON 직렬화 가능한 타입으로 변환"""
            if hasattr(obj, 'item'):
                return obj.item()
            elif hasattr(obj, 'tolist'):
                return obj.tolist()
            raise TypeError(f'Object of type {type(obj)} is not JSON serializable')
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False, default=json_serializer)
        
        print(f"💾 결과 저장: {result_file}")
        
        return all_results


def main():
    """메인 함수 - 3단계 전처리 파이프라인 실험 실행"""
    pipeline = PreprocessingPipeline()
    results = pipeline.run_pipeline_experiment()
    
    if results:
        print(f"\n🎉 모든 파이프라인 실험 완료! 총 {len(results)}개 이미지 처리")
    else:
        print(f"\n❌ 실험할 이미지가 없습니다.")


if __name__ == "__main__":
    main() 