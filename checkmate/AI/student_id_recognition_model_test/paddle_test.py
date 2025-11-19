#!/usr/bin/env python3
"""
크롭된 이미지들을 PaddleOCR로 인식하여 학번 추출
PP-StructureV3 → PaddleOCR(단순 OCR)로 변경: 문서 구조 분석 없이 텍스트 인식만 수행
"""
import os
import json
import re
from paddleocr import PaddleOCR

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
CROP_IMAGE_DIR = os.path.join(EXP_BASE_DIR, "crop_img")
OUTPUT_JSON = os.path.join(EXP_BASE_DIR, "paddle_results.json")


def is_eight_digits(text):
    """텍스트가 8자리 숫자인지 확인"""
    # 숫자만 추출
    digits = re.sub(r'\D', '', text)
    return len(digits) == 8 and digits.isdigit()


def recognize_image(image_path: str, ocr: PaddleOCR):
    """
    PaddleOCR을 사용하여 이미지에서 텍스트 인식
    
    Args:
        image_path: 인식할 이미지 경로
        ocr: PaddleOCR 인스턴스
    
    Returns:
        dict: {
            "result": 원본 인식 텍스트,
            "digits": 숫자만 추출한 문자열,
            "is_eight_digits": 8자리 숫자 여부
        }
    """
    try:
        # PaddleOCR의 predict() 메서드 사용 (ocr()는 deprecated)
        result = ocr.predict(image_path)
        
        if not result or len(result) == 0:
            return {
                "result": "",
                "digits": "",
                "is_eight_digits": False
            }
        
        # 첫 번째 결과에서 텍스트 추출
        res = result[0]
        texts = []
        
        # JSON 결과에서 rec_texts 추출
        if hasattr(res, 'json') and res.json:
            json_data = res.json
            if 'res' in json_data and 'rec_texts' in json_data['res']:
                rec_texts = json_data['res']['rec_texts']
                if isinstance(rec_texts, list):
                    texts = [str(t) for t in rec_texts if t]
                elif isinstance(rec_texts, str):
                    texts = [rec_texts] if rec_texts else []
        
        # 모든 텍스트를 공백으로 결합
        raw_text = " ".join(texts).strip()
        
        # 숫자만 추출
        digits = re.sub(r'\D', '', raw_text)
        is_valid = is_eight_digits(raw_text)
        
        return {
            "result": raw_text,
            "digits": digits,
            "is_eight_digits": is_valid
        }
        
    except Exception as e:
        print(f"  OCR 처리 오류: {e}")
        import traceback
        traceback.print_exc()
        return {
            "result": "",
            "digits": "",
            "is_eight_digits": False
        }


def main():
    print("="*60)
    print("PaddleOCR 인식 테스트")
    print("="*60)
    
    # PaddleOCR 초기화 (단순 OCR만 사용, 문서 구조 분석 없음)
    print("PaddleOCR 초기화 중...")
    ocr = PaddleOCR(
        use_textline_orientation=False,  # 숫자만 있을 때 각도 분류 불필요 (use_angle_cls 대체)
        lang='en',                       # 숫자 + 영문 인식 (한글 필요시 'korean'으로 변경)
        device='cpu'                     # CPU 모드 (use_gpu 대신 device 사용)
        # ocr_version='PP-OCRv5'         # 기본값이 PP-OCRv5이므로 생략 가능
    )
    print("✓ PaddleOCR 초기화 완료")
    
    # 크롭된 이미지 디렉토리 확인
    if not os.path.exists(CROP_IMAGE_DIR):
        print(f"❌ 크롭된 이미지 디렉토리를 찾을 수 없습니다: {CROP_IMAGE_DIR}")
        return
    
    # 크롭된 이미지 찾기
    crop_files = sorted([
        f for f in os.listdir(CROP_IMAGE_DIR)
        if f.endswith('_crop.jpg')
    ])
    
    if not crop_files:
        print(f"❌ 크롭된 이미지를 찾을 수 없습니다: {CROP_IMAGE_DIR}")
        return
    
    print(f"\n처리할 이미지 수: {len(crop_files)}")
    
    # 각 이미지 인식
    results = {}
    for crop_file in crop_files:
        image_path = os.path.join(CROP_IMAGE_DIR, crop_file)
        print(f"\n처리 중: {crop_file}")
        
        try:
            result = recognize_image(image_path, ocr)
            results[crop_file] = {
                "result": result["result"],
                "digits": result["digits"],
                "is_eight_digits": result["is_eight_digits"]
            }
            print(f"  결과: {result['result']}")
            print(f"  숫자: {result['digits']}")
            print(f"  8자리 숫자: {result['is_eight_digits']}")
        except Exception as e:
            print(f"❌ {crop_file} 처리 실패: {e}")
            results[crop_file] = {
                "result": "",
                "digits": "",
                "is_eight_digits": False
            }
    
    # JSON 저장
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✓ 결과 저장: {OUTPUT_JSON}")
    print(f"총 처리: {len(results)}개")
    
    # 요약 통계
    success_count = sum(1 for r in results.values() if r['is_eight_digits'])
    print(f"8자리 숫자 인식 성공: {success_count}/{len(results)}")


if __name__ == '__main__':
    main()
