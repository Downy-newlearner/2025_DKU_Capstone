#!/usr/bin/env python3
"""
OCR과 YOLOv8 모델 테스트 스크립트
main.py에서 사용하는 모델을 그대로 사용하여 단일 이미지 테스트
"""
import os
import sys
import logging
from pathlib import Path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# 경로 설정
sys.path.insert(0, os.path.dirname(__file__))

# main.py에서 모델 로드 함수 import
from student_id_recognition.main import (
    get_yolo_model,
    get_ocr_model,
    preprocess_for_ocr,
    parse_ocr_result,
    STUDENT_ID_PATTERN,
    STUDENT_ID_CLASS_ID
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_yolo_model(image_path: str, yolo_model):
    """
    YOLO 모델 테스트
    
    Args:
        image_path: 테스트할 이미지 경로
        yolo_model: YOLO 모델 객체
    """
    print("\n" + "="*60)
    print("YOLO 모델 테스트")
    print("="*60)
    
    # 이미지 로드
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    print(f"이미지 크기: {image.size}")
    print(f"이미지 모드: {image.mode}")
    
    # YOLO 추론
    print("\nYOLO 추론 수행 중...")
    results = yolo_model(image, verbose=False, conf=0.1)  # 낮은 임계값으로 모든 박스 검출
    
    # 결과 분석
    all_boxes = []
    detected_classes = set()
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            class_id = int(box.cls)
            confidence = float(box.conf)
            detected_classes.add(class_id)
            
            xyxy = box.xyxy[0].tolist()
            x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
            
            all_boxes.append({
                "class_id": class_id,
                "confidence": confidence,
                "bbox": (x1, y1, x2, y2)
            })
    
    print(f"\n검출된 박스 수: {len(all_boxes)}")
    print(f"검출된 클래스: {detected_classes}")
    
    if all_boxes:
        print("\n검출된 박스 상세 정보:")
        for i, box in enumerate(all_boxes[:10], 1):  # 처음 10개만 출력
            print(f"  {i}. Class ID: {box['class_id']}, "
                  f"Confidence: {box['confidence']:.3f}, "
                  f"BBox: {box['bbox']}")
        
        # 학번 영역 필터링
        student_id_boxes = [
            box for box in all_boxes 
            if box['class_id'] == STUDENT_ID_CLASS_ID or box['confidence'] > 0.3
        ]
        print(f"\n학번 영역 후보 (class_id={STUDENT_ID_CLASS_ID} or conf>0.3): {len(student_id_boxes)}")
        
        if student_id_boxes:
            best_box = max(student_id_boxes, key=lambda x: x["confidence"])
            print(f"최고 신뢰도 박스:")
            print(f"  Class ID: {best_box['class_id']}")
            print(f"  Confidence: {best_box['confidence']:.3f}")
            print(f"  BBox: {best_box['bbox']}")
            
            # 이미지에 박스 그리기
            fig, ax = plt.subplots(1, 1, figsize=(12, 8))
            ax.imshow(image)
            
            # 모든 박스 그리기 (반투명)
            for box in all_boxes:
                x1, y1, x2, y2 = box['bbox']
                rect = patches.Rectangle(
                    (x1, y1), x2-x1, y2-y1,
                    linewidth=1, edgecolor='blue', facecolor='none', alpha=0.3
                )
                ax.add_patch(rect)
            
            # 학번 영역 후보 강조
            for box in student_id_boxes:
                x1, y1, x2, y2 = box['bbox']
                rect = patches.Rectangle(
                    (x1, y1), x2-x1, y2-y1,
                    linewidth=2, edgecolor='green', facecolor='none'
                )
                ax.add_patch(rect)
                ax.text(x1, y1-5, f"Class:{box['class_id']} Conf:{box['confidence']:.2f}",
                       color='green', fontsize=8, weight='bold')
            
            # 최고 신뢰도 박스 강조
            x1, y1, x2, y2 = best_box['bbox']
            rect = patches.Rectangle(
                (x1, y1), x2-x1, y2-y1,
                linewidth=3, edgecolor='red', facecolor='none'
            )
            ax.add_patch(rect)
            ax.text(x1, y1-10, f"BEST: Class:{best_box['class_id']} Conf:{best_box['confidence']:.3f}",
                   color='red', fontsize=10, weight='bold')
            
            ax.set_title(f"YOLO Detection Results (Total: {len(all_boxes)} boxes)")
            ax.axis('off')
            
            output_path = os.path.join(os.path.dirname(image_path), "yolo_detection_result.jpg")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"\n결과 이미지 저장: {output_path}")
            plt.close()
            
            return best_box
        else:
            print("\n⚠️ 학번 영역 후보가 없습니다.")
            return None
    else:
        print("\n⚠️ 검출된 박스가 없습니다.")
        return None


def test_ocr_model(image_path: str, ocr_model, crop_box=None):
    """
    OCR 모델 테스트
    
    Args:
        image_path: 테스트할 이미지 경로
        ocr_model: OCR 모델 객체
        crop_box: 크롭할 영역 (bbox) - None이면 전체 이미지
    """
    print("\n" + "="*60)
    print("OCR 모델 테스트")
    print("="*60)
    
    # 이미지 로드
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 크롭 영역이 있으면 크롭
    if crop_box:
        x1, y1, x2, y2 = crop_box['bbox']
        cropped_image = image.crop((x1, y1, x2, y2))
        print(f"크롭 영역: ({x1}, {y1}, {x2}, {y2})")
        print(f"크롭된 이미지 크기: {cropped_image.size}")
        test_image = cropped_image
    else:
        print("전체 이미지에서 OCR 수행")
        test_image = image
    
    # OCR 전처리
    print("\nOCR 전처리 수행 중...")
    preprocessed_image = preprocess_for_ocr(test_image)
    
    # OCR 수행 (main.py와 동일한 방식)
    print("OCR 수행 중...")
    # PIL Image를 numpy array로 변환 (main.py와 동일)
    cropped_array = np.array(preprocessed_image)
    
    # 이미지 배열 형식 확인 및 수정
    if len(cropped_array.shape) == 2:
        # 그레이스케일인 경우 RGB로 변환
        cropped_array = np.stack([cropped_array] * 3, axis=-1)
    
    # main.py에서 사용하는 방식과 동일하게
    try:
        # PaddleOCR의 ocr 메서드 사용 (main.py와 동일)
        ocr_results = ocr_model.ocr(cropped_array, cls=True)
    except (TypeError, AttributeError) as e:
        # cls 인자가 없거나 다른 오류인 경우
        print(f"  Warning: ocr() with cls failed: {e}")
        try:
            ocr_results = ocr_model.ocr(cropped_array)
        except Exception as e2:
            print(f"  Warning: ocr() without cls failed: {e2}")
            # 이미지 경로로 직접 전달 시도
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                test_image.save(tmp.name)
                ocr_results = ocr_model.ocr(tmp.name)
                os.unlink(tmp.name)
    
    # 결과 파싱
    recognized_text, ocr_confidence = parse_ocr_result(ocr_results)
    
    print(f"\nOCR 결과:")
    print(f"  인식된 텍스트: '{recognized_text}'")
    print(f"  평균 신뢰도: {ocr_confidence:.3f}")
    
    # 원본 OCR 결과 출력
    if ocr_results:
        print(f"\n원본 OCR 결과 (처음 5개):")
        for i, line_result in enumerate(ocr_results[0][:5], 1):
            if isinstance(line_result, list) and len(line_result) >= 2:
                text_info = line_result[1]
                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                    text = str(text_info[0])
                    conf = float(text_info[1])
                    print(f"  {i}. '{text}' (신뢰도: {conf:.3f})")
    
    # 8자리 학번 추출
    student_id_match = STUDENT_ID_PATTERN.search(recognized_text)
    if student_id_match:
        recognized_student_id = student_id_match.group()
        print(f"\n✓ 8자리 학번 추출 성공: {recognized_student_id}")
        return recognized_student_id, ocr_confidence
    else:
        print(f"\n⚠️ 8자리 학번을 찾을 수 없습니다.")
        print(f"  추출된 숫자: '{recognized_text}'")
        return None, ocr_confidence


def main():
    """메인 테스트 함수"""
    # 테스트 이미지 경로
    image_path = "/Users/downy/Documents/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/legacy/신호및시스템-50/신호및시스템-50 2/학생 답지 - 1.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ 이미지 파일을 찾을 수 없습니다: {image_path}")
        return
    
    print("="*60)
    print("OCR 및 YOLOv8 모델 테스트")
    print("="*60)
    print(f"테스트 이미지: {image_path}")
    
    # 모델 로드
    print("\n모델 로드 중...")
    yolo_model = get_yolo_model()
    if yolo_model is None:
        print("❌ YOLO 모델 로드 실패")
        return
    
    ocr_model = get_ocr_model()
    if ocr_model is None:
        print("❌ OCR 모델 로드 실패")
        return
    
    print("✓ 모델 로드 완료")
    
    # YOLO 테스트
    best_box = test_yolo_model(image_path, yolo_model)
    
    # OCR 테스트 (크롭된 영역)
    if best_box:
        print("\n" + "-"*60)
        print("크롭된 영역에서 OCR 수행")
        print("-"*60)
        student_id, ocr_conf = test_ocr_model(image_path, ocr_model, crop_box=best_box)
    else:
        print("\n" + "-"*60)
        print("전체 이미지에서 OCR 수행 (YOLO 실패)")
        print("-"*60)
        student_id, ocr_conf = test_ocr_model(image_path, ocr_model, crop_box=None)
    
    # 최종 결과
    print("\n" + "="*60)
    print("최종 결과")
    print("="*60)
    if student_id:
        print(f"✓ 학번 인식 성공: {student_id}")
        print(f"  OCR 신뢰도: {ocr_conf:.3f}")
    else:
        print("❌ 학번 인식 실패")
    
    print("\n테스트 완료!")


if __name__ == '__main__':
    main()

