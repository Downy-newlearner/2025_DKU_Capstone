# 필요한 라이브러리 임포트
from PIL import Image
import sys
import os

# digit_recognizer.py가 있는 경로를 Python path에 추가
# (실제 프로젝트 구조에 맞게 경로 수정 필요)
sys.path.append('/path/to/checkmate/AI/answer_recognition/recognition')

# digit_recognizer.py에서 필요한 함수들 임포트
from digit_recognizer import (
    pil_find_digit_contours_in_text_crop,
    pil_recognize_single_digit,
    pil_recognize_digits_from_bboxes,
    group_and_combine_digits
)

def recognize_digits_from_image(pil_image, expected_answer_count=1):
    """
    PIL 이미지에서 숫자를 인식하는 메인 함수
    
    Args:
        pil_image: PIL Image 객체 (단일 숫자 또는 여러 숫자가 포함된 이미지)
        expected_answer_count: 예상되는 답안 개수 (기본값: 1)
    
    Returns:
        dict: 인식 결과와 신뢰도 정보
    """
    
    # 1. 단일 숫자 이미지인 경우 직접 인식 시도
    if is_single_digit_image(pil_image):
        result = pil_recognize_single_digit(pil_image)
        if result:
            return {
                'status': 'success',
                'recognized_numbers': [result['text']],
                'confidence': result['confidence'],
                'method': 'single_digit_recognition'
            }
        else:
            return {
                'status': 'failure',
                'reason': 'Single digit recognition failed',
                'confidence': 0.0
            }
    
    # 2. 여러 숫자가 포함된 이미지인 경우
    else:
        # 2-1. 숫자 윤곽선 검출
        digit_bboxes = pil_find_digit_contours_in_text_crop(pil_image, min_contour_area=3)
        
        if not digit_bboxes:
            return {
                'status': 'failure',
                'reason': 'No digit contours found',
                'confidence': 0.0
            }
        
        # 2-2. 각 바운딩 박스 내 숫자 인식
        recognized_digits = pil_recognize_digits_from_bboxes(pil_image, digit_bboxes)
        
        if not recognized_digits:
            return {
                'status': 'failure',
                'reason': 'No digits recognized from bounding boxes',
                'confidence': 0.0
            }
        
        # 2-3. 신뢰도 계산
        confidences = [digit['confidence'] for digit in recognized_digits]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        min_confidence = min(confidences) if confidences else 0.0
        
        # 2-4. 숫자 그룹화 및 결합
        # 간격 임계값 계산 (이미지 너비의 10% 정도)
        max_spacing_threshold = pil_image.width * 0.1
        
        # 전역 좌표계로 변환 (여기서는 단순화)
        globally_sorted_digits = []
        for digit in recognized_digits:
            globally_sorted_digits.append({
                'text': digit['text'],
                'confidence': digit['confidence'],
                'global_x_center': digit['center_x_in_text_crop'],
                'digit_width': digit['bbox_in_text_crop'][2]  # width
            })
        
        # x좌표 기준으로 정렬
        globally_sorted_digits.sort(key=lambda d: d['global_x_center'])
        
        # 숫자 그룹화
        combined_numbers = group_and_combine_digits(
            globally_sorted_digits, 
            max_spacing_threshold, 
            expected_answer_count
        )
        
        return {
            'status': 'success',
            'recognized_numbers': combined_numbers,
            'confidence': avg_confidence,
            'min_confidence': min_confidence,
            'individual_digits': [
                {
                    'text': digit['text'],
                    'confidence': digit['confidence'],
                    'position': (digit['center_x_in_text_crop'], digit['center_y_in_text_crop'])
                }
                for digit in recognized_digits
            ],
            'method': 'multi_digit_recognition'
        }

def is_single_digit_image(pil_image, size_threshold=50):
    """
    이미지가 단일 숫자인지 판단하는 헬퍼 함수
    
    Args:
        pil_image: PIL Image 객체
        size_threshold: 단일 숫자로 판단할 크기 임계값
    
    Returns:
        bool: 단일 숫자 이미지 여부
    """
    # 간단한 휴리스틱: 이미지가 작고 정사각형에 가까우면 단일 숫자로 판단
    width, height = pil_image.size
    aspect_ratio = width / height if height > 0 else 1
    
    return (max(width, height) < size_threshold and 
            0.5 <= aspect_ratio <= 2.0)

# 사용 예제
def main():
    """사용 예제"""
    
    # 예제 1: 단일 숫자 이미지 인식
    print("=== 예제 1: 단일 숫자 이미지 ===")
    try:
        # 이미지 로드 (실제 경로로 변경 필요)
        single_digit_image = Image.open("path/to/single_digit.jpg")
        
        result = recognize_digits_from_image(single_digit_image)
        
        print(f"상태: {result['status']}")
        if result['status'] == 'success':
            print(f"인식된 숫자: {result['recognized_numbers']}")
            print(f"신뢰도: {result['confidence']:.3f}")
            print(f"인식 방법: {result['method']}")
        else:
            print(f"실패 이유: {result['reason']}")
            
    except Exception as e:
        print(f"단일 숫자 이미지 처리 중 오류: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # 예제 2: 여러 숫자가 포함된 이미지 인식
    print("=== 예제 2: 여러 숫자 이미지 ===")
    try:
        # 이미지 로드 (실제 경로로 변경 필요)
        multi_digit_image = Image.open("path/to/multi_digits.jpg")
        
        # 예상 답안 개수 2개로 설정(문제 번호든 답안이든 항상 1개니까 사용할 때는 1로 설정하면 되겠지! 이 코드는 파라미터 이해를 도우려고 이렇게 작성했어.)
        result = recognize_digits_from_image(multi_digit_image, expected_answer_count=2)
        
        print(f"상태: {result['status']}")
        if result['status'] == 'success':
            print(f"인식된 숫자: {result['recognized_numbers']}")
            print(f"평균 신뢰도: {result['confidence']:.3f}")
            print(f"최소 신뢰도: {result['min_confidence']:.3f}")
            print(f"인식 방법: {result['method']}")
            
            print("\n개별 숫자 상세:")
            for i, digit in enumerate(result['individual_digits']):
                print(f"  {i+1}. 숫자: {digit['text']}, "
                      f"신뢰도: {digit['confidence']:.3f}, "
                      f"위치: {digit['position']}")
        else:
            print(f"실패 이유: {result['reason']}")
            
    except Exception as e:
        print(f"여러 숫자 이미지 처리 중 오류: {e}")

# 간단한 테스트 함수
def test_with_sample_image():
    """샘플 이미지로 테스트"""
    try:
        # 흰 배경에 검은 글씨로 간단한 테스트 이미지 생성
        from PIL import ImageDraw, ImageFont
        
        # 테스트 이미지 생성 (100x50 크기)
        test_image = Image.new('RGB', (100, 50), color='white')
        draw = ImageDraw.Draw(test_image)
        
        # 숫자 그리기 (폰트가 없으면 기본 폰트 사용)
        try:
            # 시스템 폰트 시도
            font = ImageFont.truetype("arial.ttf", 30)
        except:
            font = ImageFont.load_default()
        
        draw.text((10, 10), "123", fill='black', font=font)
        
        print("=== 생성된 테스트 이미지 인식 ===")
        result = recognize_digits_from_image(test_image, expected_answer_count=1)
        
        print(f"상태: {result['status']}")
        if result['status'] == 'success':
            print(f"인식된 숫자: {result['recognized_numbers']}")
            print(f"신뢰도: {result.get('confidence', 0):.3f}")
        else:
            print(f"실패 이유: {result['reason']}")
            
    except Exception as e:
        print(f"테스트 이미지 생성/처리 중 오류: {e}")

if __name__ == "__main__":
    # 실제 이미지 파일이 있는 경우
    # main()
    
    # 테스트 이미지로 실행
    test_with_sample_image()