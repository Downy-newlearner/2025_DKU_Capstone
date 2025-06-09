"""
YOLO를 사용한 답안 영역 추출 모듈
"""

import cv2
import os
from pathlib import Path
from typing import List, Optional
from ultralytics import YOLO
from PIL import Image

from config import (
    YOLO_MODEL_PATH, YOLO_CLASS_ANSWER,
    ORIGINAL_IMAGES_DIR, YOLO_ANSWER_IMAGES_DIR,
    IMAGE_EXTENSIONS
)


class YOLOAnswerExtractor:
    """YOLO를 사용해서 시험지에서 답안 영역을 추출하는 클래스"""
    
    def __init__(self, model_path: str = None):
        """
        YOLO 추출기 초기화
        
        Args:
            model_path: YOLO 모델 파일 경로
        """
        self.model_path = model_path or YOLO_MODEL_PATH
        self.model = None
        self._load_model()
        
        # 출력 디렉토리 생성
        YOLO_ANSWER_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    def _load_model(self):
        """YOLO 모델 로드"""
        try:
            self.model = YOLO(self.model_path)
            print(f"✅ YOLO 모델 로드 완료: {self.model_path}")
        except Exception as e:
            print(f"❌ YOLO 모델 로드 실패: {e}")
            self.model = None
    
    def extract_answer_area(self, image_path: Path) -> Optional[Path]:
        """
        단일 이미지에서 답안 영역 추출
        
        Args:
            image_path: 원본 이미지 경로
            
        Returns:
            추출된 답안 이미지 경로 (추출 실패시 None)
        """
        if not self.model:
            print("❌ YOLO 모델이 로드되지 않았습니다.")
            return None
        
        try:
            # 이미지 로드
            image = cv2.imread(str(image_path))
            if image is None:
                print(f"❌ 이미지 로드 실패: {image_path}")
                return None
            
            # YOLO 추론
            results = self.model(image, verbose=False)
            
            # 답안 영역 찾기
            answer_bbox = None
            max_confidence = 0
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        class_id = int(box.cls)
                        confidence = float(box.conf)
                        
                        # 답안 클래스이고 신뢰도가 높은 것 선택
                        if class_id == YOLO_CLASS_ANSWER and confidence > max_confidence:
                            max_confidence = confidence
                            xyxy = box.xyxy[0].tolist()
                            answer_bbox = [int(x) for x in xyxy]  # [x1, y1, x2, y2]
            
            if answer_bbox is None:
                print(f"⚠️  답안 영역을 찾지 못함: {image_path.name}")
                return None
            
            # 답안 영역 크롭
            x1, y1, x2, y2 = answer_bbox
            answer_image = image[y1:y2, x1:x2]
            
            # 저장
            output_path = YOLO_ANSWER_IMAGES_DIR / f"{image_path.stem}_answer.jpg"
            cv2.imwrite(str(output_path), answer_image)
            
            print(f"✅ 답안 영역 추출 완료: {image_path.name} → {output_path.name} (신뢰도: {max_confidence:.3f})")
            return output_path
            
        except Exception as e:
            print(f"❌ 답안 영역 추출 중 오류 발생 {image_path.name}: {e}")
            return None
    
    def extract_all_answer_areas(self, input_dir: Path = None) -> List[Path]:
        """
        디렉토리 내 모든 이미지에서 답안 영역 추출
        
        Args:
            input_dir: 입력 디렉토리 (기본값: ORIGINAL_IMAGES_DIR)
            
        Returns:
            추출된 답안 이미지 경로 리스트
        """
        input_dir = input_dir or ORIGINAL_IMAGES_DIR
        
        if not input_dir.exists():
            print(f"❌ 입력 디렉토리가 존재하지 않습니다: {input_dir}")
            return []
        
        # 이미지 파일 찾기
        image_files = []
        for ext in IMAGE_EXTENSIONS:
            image_files.extend(input_dir.glob(f"*{ext}"))
            image_files.extend(input_dir.glob(f"*{ext.upper()}"))
        
        if not image_files:
            print(f"❌ 이미지 파일을 찾을 수 없습니다: {input_dir}")
            return []
        
        print(f"📁 총 {len(image_files)}개의 이미지 파일 발견")
        
        # 답안 영역 추출
        extracted_paths = []
        for i, image_path in enumerate(image_files, 1):
            print(f"\n[{i}/{len(image_files)}] 처리 중: {image_path.name}")
            
            extracted_path = self.extract_answer_area(image_path)
            if extracted_path:
                extracted_paths.append(extracted_path)
        
        print(f"\n🎯 총 {len(extracted_paths)}개의 답안 영역 추출 완료")
        print(f"📂 저장 위치: {YOLO_ANSWER_IMAGES_DIR}")
        
        return extracted_paths


def main():
    """메인 함수 - 답안 영역 추출 실행"""
    print("=" * 60)
    print("YOLO 답안 영역 추출 시작")
    print("=" * 60)
    
    extractor = YOLOAnswerExtractor()
    extracted_paths = extractor.extract_all_answer_areas()
    
    if extracted_paths:
        print(f"\n✅ 모든 처리 완료! 추출된 이미지: {len(extracted_paths)}개")
    else:
        print(f"\n❌ 추출된 이미지가 없습니다.")


if __name__ == "__main__":
    main() 