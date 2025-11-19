#!/usr/bin/env python3
"""
YOLOv8 모델 테스트 스크립트
학번 영역 검출 모델을 테스트하고 결과를 시각화
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from ultralytics import YOLO

# 모델 경로
MODEL_PATH = "/home/jdh251425/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/student_id_recognition/model/best_student_id.pt"

# 테스트 이미지 디렉토리
TEST_IMAGE_DIR = "/home/jdh251425/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/Data/인공지능 중간고사 2023"

# 결과 저장 디렉토리
SCRIPT_DIR = os.path.dirname(__file__)
EXP_NUMBER = int(os.environ.get('EXPERIMENT_NUMBER', '1'))

def get_ordinal_suffix(n):
    """숫자를 ordinal 형식으로 변환 (1st, 2nd, 3rd, 4th...)"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

EXP_NAME = get_ordinal_suffix(EXP_NUMBER)
EXP_BASE_DIR = os.path.join(SCRIPT_DIR, "exp", EXP_NAME)
OUTPUT_DIR = os.path.join(EXP_BASE_DIR, "yolo_result")

# YOLO 설정
STUDENT_ID_CLASS_ID = 0  # 학번 영역 클래스 ID
CONF_THRESHOLD = 0.1  # 낮은 임계값으로 모든 박스 검출


def load_yolo_model(model_path: str):
    """YOLO 모델 로드 (CPU 모드)"""
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"모델 파일을 찾을 수 없습니다: {model_path}")
    
    print(f"모델 로드 중: {model_path}")
    # CPU 모드로 강제 설정 (CUDA 호환성 문제 해결)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    model = YOLO(model_path)
    # 모델을 CPU로 이동
    model.to('cpu')
    print("✓ 모델 로드 완료 (CPU 모드)")
    return model


def test_single_image(image_path: str, yolo_model, output_dir: str):
    """
    단일 이미지에 대해 YOLO 모델 테스트 및 시각화
    
    Args:
        image_path: 테스트할 이미지 경로
        yolo_model: YOLO 모델 객체
        output_dir: 결과 이미지 저장 디렉토리
    """
    print(f"\n{'='*60}")
    print(f"이미지 처리: {os.path.basename(image_path)}")
    print(f"{'='*60}")
    
    # 이미지 로드
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    print(f"이미지 크기: {image.size}")
    
    # YOLO 추론 (CPU 모드)
    print("YOLO 추론 수행 중...")
    results = yolo_model(image, verbose=False, conf=CONF_THRESHOLD, device='cpu')
    
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
    
    print(f"검출된 박스 수: {len(all_boxes)}")
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
    else:
        print("\n⚠️ 검출된 박스가 없습니다.")
        student_id_boxes = []
        best_box = None
    
    # 시각화
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
               color='green', fontsize=8, weight='bold', 
               bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
    
    # 최고 신뢰도 박스 강조
    if best_box:
        x1, y1, x2, y2 = best_box['bbox']
        rect = patches.Rectangle(
            (x1, y1), x2-x1, y2-y1,
            linewidth=3, edgecolor='red', facecolor='none'
        )
        ax.add_patch(rect)
        ax.text(x1, y1-10, f"BEST: Class:{best_box['class_id']} Conf:{best_box['confidence']:.3f}",
               color='red', fontsize=10, weight='bold',
               bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.8))
    
    ax.set_title(f"YOLO Detection Results - {os.path.basename(image_path)}\n"
                f"Total: {len(all_boxes)} boxes, Student ID candidates: {len(student_id_boxes)}",
                fontsize=12, weight='bold')
    ax.axis('off')
    
    # 결과 이미지 저장
    output_filename = f"yolo_result_{os.path.splitext(os.path.basename(image_path))[0]}.jpg"
    output_path = os.path.join(output_dir, output_filename)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n✓ 결과 이미지 저장: {output_path}")
    plt.close()
    
    # 바운딩박스 정보를 JSON 파일로 저장
    json_filename = f"yolo_result_{os.path.splitext(os.path.basename(image_path))[0]}.json"
    json_path = os.path.join(output_dir, json_filename)
    
    bbox_data = {
        "image_path": image_path,
        "image_size": list(image.size),
        "all_boxes": [
            {
                "class_id": box["class_id"],
                "confidence": float(box["confidence"]),
                "bbox": list(box["bbox"])
            }
            for box in all_boxes
        ],
        "student_id_candidates": [
            {
                "class_id": box["class_id"],
                "confidence": float(box["confidence"]),
                "bbox": list(box["bbox"])
            }
            for box in student_id_boxes
        ],
        "best_box": {
            "class_id": int(best_box["class_id"]),
            "confidence": float(best_box["confidence"]),
            "bbox": list(best_box["bbox"])
        } if best_box else None
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(bbox_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ 바운딩박스 정보 저장: {json_filename}")
    
    return {
        "image": os.path.basename(image_path),
        "total_boxes": len(all_boxes),
        "student_id_candidates": len(student_id_boxes),
        "best_box": best_box
    }


def main():
    """메인 테스트 함수"""
    # CUDA 비활성화 (CPU 모드로 실행)
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    print("="*60)
    print("YOLOv8 학번 영역 검출 모델 테스트 (CPU 모드)")
    print("="*60)
    
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"결과 저장 위치: {OUTPUT_DIR}")
    
    # 모델 로드
    try:
        yolo_model = load_yolo_model(MODEL_PATH)
    except Exception as e:
        print(f"❌ 모델 로드 실패: {e}")
        return
    
    # 테스트 이미지 목록 가져오기
    if not os.path.exists(TEST_IMAGE_DIR):
        print(f"❌ 테스트 이미지 디렉토리를 찾을 수 없습니다: {TEST_IMAGE_DIR}")
        return
    
    image_files = sorted([
        f for f in os.listdir(TEST_IMAGE_DIR)
        if f.lower().endswith(('.jpg', '.jpeg', '.png'))
    ])
    
    if not image_files:
        print(f"❌ 테스트 이미지를 찾을 수 없습니다: {TEST_IMAGE_DIR}")
        return
    
    print(f"\n테스트 이미지 디렉토리: {TEST_IMAGE_DIR}")
    print(f"발견된 이미지 수: {len(image_files)}")
    
    # 각 이미지 테스트
    results = []
    for i, image_file in enumerate(image_files[:10], 1):  # 최대 10장
        image_path = os.path.join(TEST_IMAGE_DIR, image_file)
        try:
            result = test_single_image(image_path, yolo_model, OUTPUT_DIR)
            results.append(result)
        except Exception as e:
            print(f"❌ 이미지 처리 중 오류 발생 ({image_file}): {e}")
            continue
    
    # 최종 요약
    print("\n" + "="*60)
    print("테스트 결과 요약")
    print("="*60)
    print(f"처리된 이미지 수: {len(results)}")
    
    total_boxes = sum(r['total_boxes'] for r in results)
    total_candidates = sum(r['student_id_candidates'] for r in results)
    success_count = sum(1 for r in results if r['best_box'] is not None)
    
    print(f"총 검출된 박스 수: {total_boxes}")
    print(f"학번 영역 후보 수: {total_candidates}")
    print(f"학번 영역 검출 성공: {success_count}/{len(results)}")
    
    print(f"\n결과 이미지 저장 위치: {OUTPUT_DIR}")
    print("\n테스트 완료!")


if __name__ == '__main__':
    main()

