"""
EasyOCR 기준선 실험 및 시각화 모듈
"""

import cv2
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
import easyocr
import numpy as np

from config import (
    YOLO_ANSWER_IMAGES_DIR, EASYOCR_RESULTS_DIR, VISUALIZATION_DIR,
    EASYOCR_LANGUAGES, EASYOCR_CONFIDENCE_THRESHOLD,
    BBOX_COLOR, BBOX_THICKNESS, TEXT_COLOR, TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS
)


class EasyOCRBaseline:
    """EasyOCR 기준선 실험 클래스"""
    
    def __init__(self):
        """EasyOCR 기준선 실험 초기화"""
        self.reader = None
        self._init_reader()
        
        # 출력 디렉토리 생성
        EASYOCR_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        VISUALIZATION_DIR.mkdir(parents=True, exist_ok=True)
    
    def _init_reader(self):
        """EasyOCR 리더 초기화"""
        try:
            print("🔄 EasyOCR 초기화 중...")
            self.reader = easyocr.Reader(EASYOCR_LANGUAGES)
            print("✅ EasyOCR 초기화 완료")
        except Exception as e:
            print(f"❌ EasyOCR 초기화 실패: {e}")
            self.reader = None
    
    def process_single_image(self, image_path: Path) -> Dict[str, Any]:
        """
        단일 이미지에 EasyOCR 적용
        
        Args:
            image_path: 답안 이미지 경로
            
        Returns:
            OCR 결과 딕셔너리
        """
        if not self.reader:
            return {"error": "EasyOCR 리더가 초기화되지 않았습니다."}
        
        try:
            # 이미지 로드
            image = cv2.imread(str(image_path))
            if image is None:
                return {"error": f"이미지 로드 실패: {image_path}"}
            
            # EasyOCR 적용
            start_time = time.time()
            results = self.reader.readtext(str(image_path))
            processing_time = time.time() - start_time
            
            # 결과 정리
            ocr_results = []
            for (bbox, text, confidence) in results:
                if confidence >= EASYOCR_CONFIDENCE_THRESHOLD:
                    # bbox를 정수로 변환 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]] → [x1,y1,x2,y2]
                    bbox_coords = np.array(bbox).astype(int)
                    x1, y1 = bbox_coords[0]
                    x2, y2 = bbox_coords[2]
                    
                    ocr_results.append({
                        "text": text,
                        "confidence": float(confidence),
                        "bbox": [int(x1), int(y1), int(x2), int(y2)]
                    })
            
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "processing_time": processing_time,
                "num_detections": len(ocr_results),
                "detections": ocr_results,
                "success": True
            }
            
        except Exception as e:
            return {
                "image_path": str(image_path),
                "image_name": image_path.name,
                "error": str(e),
                "success": False
            }
    
    def visualize_results(self, image_path: Path, ocr_result: Dict[str, Any]) -> Path:
        """
        OCR 결과를 이미지에 시각화
        
        Args:
            image_path: 원본 이미지 경로
            ocr_result: OCR 결과
            
        Returns:
            시각화된 이미지 저장 경로
        """
        # 이미지 로드
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"❌ 시각화용 이미지 로드 실패: {image_path}")
            return None
        
        # 사본 생성
        vis_image = image.copy()
        
        # OCR 결과가 성공적이고 탐지 결과가 있는 경우
        if ocr_result.get("success", False) and ocr_result.get("detections", []):
            for detection in ocr_result["detections"]:
                bbox = detection["bbox"]
                text = detection["text"]
                confidence = detection["confidence"]
                
                x1, y1, x2, y2 = bbox
                
                # 바운딩 박스 그리기 (초록색)
                cv2.rectangle(vis_image, (x1, y1), (x2, y2), BBOX_COLOR, BBOX_THICKNESS)
                
                # 텍스트와 신뢰도 표시 (바운딩 박스 상단)
                label = f"{text} ({confidence:.2f})"
                
                # 텍스트 배경 크기 계산
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, TEXT_FONT, TEXT_SCALE, TEXT_THICKNESS
                )
                
                # 텍스트 배경 그리기 (검은색)
                cv2.rectangle(
                    vis_image,
                    (x1, y1 - text_height - baseline - 5),
                    (x1 + text_width, y1),
                    (0, 0, 0),
                    -1
                )
                
                # 텍스트 그리기 (초록색)
                cv2.putText(
                    vis_image,
                    label,
                    (x1, y1 - baseline - 2),
                    TEXT_FONT,
                    TEXT_SCALE,
                    TEXT_COLOR,
                    TEXT_THICKNESS
                )
        
        # 결과 정보 텍스트 추가 (이미지 하단)
        info_text = f"Detections: {ocr_result.get('num_detections', 0)}, "
        info_text += f"Time: {ocr_result.get('processing_time', 0):.2f}s"
        
        cv2.putText(
            vis_image,
            info_text,
            (10, vis_image.shape[0] - 10),
            TEXT_FONT,
            TEXT_SCALE,
            (255, 255, 255),  # 흰색
            TEXT_THICKNESS
        )
        
        # 저장
        output_path = VISUALIZATION_DIR / f"{image_path.stem}_easyocr_vis.jpg"
        cv2.imwrite(str(output_path), vis_image)
        
        return output_path
    
    def run_baseline_experiment(self, input_dir: Path = None) -> List[Dict[str, Any]]:
        """
        모든 답안 이미지에 대해 EasyOCR 기준선 실험 실행
        
        Args:
            input_dir: 입력 디렉토리 (기본값: YOLO_ANSWER_IMAGES_DIR)
            
        Returns:
            모든 이미지의 OCR 결과 리스트
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
        print("EasyOCR 기준선 실험 시작")
        print("=" * 60)
        
        all_results = []
        total_processing_time = 0
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 처리 중: {image_path.name}")
            
            # OCR 적용
            ocr_result = self.process_single_image(image_path)
            all_results.append(ocr_result)
            
            if ocr_result.get("success", False):
                processing_time = ocr_result.get("processing_time", 0)
                total_processing_time += processing_time
                num_detections = ocr_result.get("num_detections", 0)
                
                print(f"   ✅ OCR 완료: {num_detections}개 탐지, {processing_time:.2f}초")
                
                # 시각화
                vis_path = self.visualize_results(image_path, ocr_result)
                if vis_path:
                    print(f"   🎨 시각화 저장: {vis_path.name}")
                
                # 탐지된 텍스트 출력
                if num_detections > 0:
                    print("   📝 탐지된 텍스트:")
                    for j, detection in enumerate(ocr_result["detections"], 1):
                        text = detection["text"]
                        confidence = detection["confidence"]
                        print(f"      {j}. '{text}' (신뢰도: {confidence:.3f})")
                
            else:
                error_msg = ocr_result.get("error", "알 수 없는 오류")
                print(f"   ❌ OCR 실패: {error_msg}")
        
        # 전체 결과 요약
        print("\n" + "=" * 60)
        print("EasyOCR 기준선 실험 완료")
        print("=" * 60)
        
        successful_results = [r for r in all_results if r.get("success", False)]
        total_detections = sum(r.get("num_detections", 0) for r in successful_results)
        avg_processing_time = total_processing_time / len(successful_results) if successful_results else 0
        
        print(f"✅ 성공한 이미지: {len(successful_results)}/{len(image_files)}")
        print(f"🎯 총 탐지 수: {total_detections}")
        print(f"⏱️  평균 처리 시간: {avg_processing_time:.2f}초")
        print(f"📂 시각화 결과: {VISUALIZATION_DIR}")
        
        # 결과를 JSON 파일로 저장
        result_file = EASYOCR_RESULTS_DIR / "easyocr_baseline_results.json"
        
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
    """메인 함수 - EasyOCR 기준선 실험 실행"""
    baseline = EasyOCRBaseline()
    results = baseline.run_baseline_experiment()
    
    if results:
        print(f"\n🎉 모든 실험 완료! 총 {len(results)}개 이미지 처리")
    else:
        print(f"\n❌ 실험할 이미지가 없습니다.")


if __name__ == "__main__":
    main() 