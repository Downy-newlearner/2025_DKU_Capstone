#!/usr/bin/env python3
"""
YOLO 결과에서 가장 신뢰도가 높은 바운딩박스를 선택하여 크롭
저장된 JSON 파일의 바운딩박스 정보를 사용하여 크롭 수행
"""
import os
import json
from PIL import Image

# 설정
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
OUTPUT_DIR = os.path.join(EXP_BASE_DIR, "crop_img")
YOLO_RESULT_DIR = os.path.join(EXP_BASE_DIR, "yolo_result")


def load_bbox_info(json_path: str) -> dict:
    """JSON 파일에서 바운딩박스 정보 로드"""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def crop_best_box(image_path: str, bbox_info: dict, output_dir: str):
    """저장된 바운딩박스 정보를 사용하여 이미지 크롭"""
    # 원본 이미지 로드
    image = Image.open(image_path)
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 바운딩박스 정보에서 best_box 추출
    best_box = bbox_info.get("best_box")
    if not best_box:
        print(f"⚠️ {os.path.basename(image_path)}: best_box 정보 없음")
        return None
    
    # 좌표 추출
    x1, y1, x2, y2 = best_box["bbox"]
    
    # 크롭
    cropped = image.crop((x1, y1, x2, y2))
    
    # 저장
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = os.path.join(output_dir, f"{base_name}_crop.jpg")
    cropped.save(output_path)
    
    print(f"✓ {os.path.basename(image_path)} → {os.path.basename(output_path)} (conf: {best_box['confidence']:.3f})")
    return output_path


def main():
    print("="*60)
    print("YOLO 결과 크롭")
    print("="*60)
    
    # 출력 디렉토리 생성
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"결과 저장 위치: {OUTPUT_DIR}")
    
    # YOLO 결과 디렉토리에서 JSON 파일 찾기
    if not os.path.exists(YOLO_RESULT_DIR):
        print(f"❌ YOLO 결과 디렉토리를 찾을 수 없습니다: {YOLO_RESULT_DIR}")
        return
    
    # JSON 파일 목록
    json_files = sorted([
        f for f in os.listdir(YOLO_RESULT_DIR)
        if f.startswith('yolo_result_') and f.endswith('.json')
    ])
    
    if not json_files:
        print(f"❌ 바운딩박스 정보 파일을 찾을 수 없습니다: {YOLO_RESULT_DIR}")
        return
    
    print(f"\n발견된 JSON 파일 수: {len(json_files)}")
    
    # 각 JSON 파일 처리
    cropped_files = []
    for json_file in json_files:
        json_path = os.path.join(YOLO_RESULT_DIR, json_file)
        
        try:
            # 바운딩박스 정보 로드
            bbox_info = load_bbox_info(json_path)
            
            # JSON에 저장된 image_path 사용
            image_path = bbox_info.get("image_path")
            if not image_path:
                print(f"⚠️ {json_file}: image_path 정보 없음")
                continue
            
            # 이미지 파일 존재 확인
            if not os.path.exists(image_path):
                print(f"⚠️ {json_file}: 원본 이미지를 찾을 수 없습니다: {image_path}")
                continue
            
            # 크롭 수행
            cropped_path = crop_best_box(image_path, bbox_info, OUTPUT_DIR)
            if cropped_path:
                cropped_files.append(cropped_path)
                
        except Exception as e:
            print(f"❌ {json_file} 처리 실패: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n크롭 완료: {len(cropped_files)}개 파일")
    print(f"저장 위치: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
