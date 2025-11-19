#!/usr/bin/env python3
"""
학번 인식 모듈 단계별 테스트 스크립트

각 단계를 독립적으로 테스트하여 문제가 있는 모듈을 빠르게 찾을 수 있습니다.
"""
import os
import sys
import logging
from pathlib import Path
from PIL import Image

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_step1_validation():
    """단계 1: 입력 검증 테스트"""
    print("\n" + "="*60)
    print("단계 1: 입력 검증 테스트")
    print("="*60)
    
    from student_id_recognition.validators import validate_inputs
    
    # 테스트 케이스 1: 정상 경로
    test_path = input("테스트할 이미지 폴더 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    logger, student_numbers, is_valid = validate_inputs(
        test_path,
        "테스트과목",
        ["12345678", "87654321"]
    )
    
    if is_valid:
        print("✓ 입력 검증 성공")
        print(f"  - 경로: {test_path}")
        print(f"  - 학번 리스트: {len(student_numbers)}개")
        return True
    else:
        print("✗ 입력 검증 실패")
        return False


def test_step2_model_loading():
    """단계 2: 모델 로드 테스트"""
    print("\n" + "="*60)
    print("단계 2: 모델 로드 테스트")
    print("="*60)
    
    from student_id_recognition.models import get_yolo_model, get_ocr_model
    
    # CUDA 비활성화
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # YOLO 모델 테스트
    print("\n2-1. YOLO 모델 로드 중...")
    try:
        yolo_model = get_yolo_model()
        if yolo_model is not None:
            print("✓ YOLO 모델 로드 성공")
        else:
            print("✗ YOLO 모델 로드 실패")
            return False
    except Exception as e:
        print(f"✗ YOLO 모델 로드 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # OCR 모델 테스트
    print("\n2-2. OCR 모델 초기화 중...")
    try:
        ocr_model = get_ocr_model()
        if ocr_model is not None:
            print("✓ OCR 모델 초기화 성공")
        else:
            print("✗ OCR 모델 초기화 실패")
            return False
    except Exception as e:
        print(f"✗ OCR 모델 초기화 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_step3_file_collection():
    """단계 3: 이미지 파일 수집 테스트"""
    print("\n" + "="*60)
    print("단계 3: 이미지 파일 수집 테스트")
    print("="*60)
    
    from student_id_recognition.file_manager import collect_image_files
    
    test_path = input("테스트할 이미지 폴더 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    try:
        image_files = collect_image_files(test_path, logger)
        if image_files:
            print(f"✓ 이미지 파일 수집 성공: {len(image_files)}개")
            print(f"  처음 5개 파일:")
            for f in image_files[:5]:
                print(f"    - {f}")
            return True
        else:
            print("✗ 이미지 파일을 찾을 수 없습니다")
            return False
    except Exception as e:
        print(f"✗ 이미지 파일 수집 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step4_image_reading():
    """단계 4-1: 이미지 읽기 테스트"""
    print("\n" + "="*60)
    print("단계 4-1: 이미지 읽기 테스트")
    print("="*60)
    
    test_path = input("테스트할 이미지 파일 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    try:
        with Image.open(test_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pil_image = img.copy()
        
        print(f"✓ 이미지 읽기 성공")
        print(f"  - 크기: {pil_image.size}")
        print(f"  - 모드: {pil_image.mode}")
        return True
    except Exception as e:
        print(f"✗ 이미지 읽기 실패: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step4_yolo_detection():
    """단계 4-2: YOLO 검출 테스트"""
    print("\n" + "="*60)
    print("단계 4-2: YOLO 검출 테스트")
    print("="*60)
    
    from student_id_recognition.models import get_yolo_model
    from student_id_recognition.yolo_detector import detect_student_id_area
    
    # CUDA 비활성화
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # 모델 로드
    yolo_model = get_yolo_model()
    if yolo_model is None:
        print("✗ YOLO 모델을 먼저 로드해야 합니다")
        return False
    
    # 이미지 경로 입력
    test_path = input("테스트할 이미지 파일 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    try:
        with Image.open(test_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pil_image = img.copy()
        
        cropped_image, yolo_confidence, yolo_error = detect_student_id_area(
            yolo_model, pil_image, os.path.basename(test_path), logger
        )
        
        if yolo_error is None:
            print(f"✓ YOLO 검출 성공")
            print(f"  - 신뢰도: {yolo_confidence:.3f}")
            if cropped_image:
                print(f"  - 크롭된 이미지 크기: {cropped_image.size}")
            return True
        else:
            print(f"✗ YOLO 검출 실패: {yolo_error}")
            return False
    except Exception as e:
        print(f"✗ YOLO 검출 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step4_ocr_recognition():
    """단계 4-3: OCR 인식 테스트"""
    print("\n" + "="*60)
    print("단계 4-3: OCR 인식 테스트")
    print("="*60)
    
    from student_id_recognition.models import get_ocr_model, get_yolo_model
    from student_id_recognition.yolo_detector import detect_student_id_area
    from student_id_recognition.ocr_processor import recognize_student_id_with_ocr
    
    # CUDA 비활성화
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # 모델 로드
    yolo_model = get_yolo_model()
    ocr_model = get_ocr_model()
    if yolo_model is None or ocr_model is None:
        print("✗ 모델을 먼저 로드해야 합니다")
        return False
    
    # 이미지 경로 입력
    test_path = input("테스트할 이미지 파일 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    try:
        # 이미지 읽기
        with Image.open(test_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pil_image = img.copy()
        
        # YOLO 검출
        print("  YOLO 검출 중...")
        cropped_image, yolo_confidence, yolo_error = detect_student_id_area(
            yolo_model, pil_image, os.path.basename(test_path), logger
        )
        
        if yolo_error is not None:
            print(f"✗ YOLO 검출 실패: {yolo_error}")
            return False
        
        # OCR 인식
        print("  OCR 인식 중...")
        recognized_student_id, ocr_confidence = recognize_student_id_with_ocr(
            ocr_model, cropped_image, os.path.basename(test_path), logger
        )
        
        if recognized_student_id:
            print(f"✓ OCR 인식 성공")
            print(f"  - 인식된 학번: {recognized_student_id}")
            print(f"  - OCR 신뢰도: {ocr_confidence:.3f}")
            return True
        else:
            print(f"⚠ OCR 인식 실패 (학번을 찾을 수 없음)")
            print(f"  - OCR 신뢰도: {ocr_confidence:.3f}")
            return False
    except Exception as e:
        print(f"✗ OCR 인식 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_single_image_full_pipeline():
    """단일 이미지 전체 파이프라인 테스트"""
    print("\n" + "="*60)
    print("단일 이미지 전체 파이프라인 테스트")
    print("="*60)
    
    from student_id_recognition.models import get_yolo_model, get_ocr_model
    from student_id_recognition.yolo_detector import detect_student_id_area
    from student_id_recognition.ocr_processor import recognize_student_id_with_ocr
    from student_id_recognition.result_handler import handle_processing_result
    
    # CUDA 비활성화
    if 'CUDA_VISIBLE_DEVICES' not in os.environ:
        os.environ['CUDA_VISIBLE_DEVICES'] = ''
    
    # 모델 로드
    print("모델 로드 중...")
    yolo_model = get_yolo_model()
    ocr_model = get_ocr_model()
    if yolo_model is None or ocr_model is None:
        print("✗ 모델 로드 실패")
        return False
    
    # 이미지 경로 입력
    test_path = input("테스트할 이미지 파일 경로를 입력하세요: ").strip()
    if not test_path:
        print("⚠ 경로를 입력하지 않았습니다. 테스트를 건너뜁니다.")
        return False
    
    extracted_path = os.path.dirname(test_path)
    image_file = os.path.basename(test_path)
    
    try:
        # 전체 파이프라인 실행
        print(f"\n이미지 처리 시작: {image_file}")
        
        # 1. 이미지 읽기
        print("  1. 이미지 읽기...")
        with Image.open(test_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            pil_image = img.copy()
        print("    ✓ 완료")
        
        # 2. YOLO 검출
        print("  2. YOLO 검출...")
        cropped_image, yolo_confidence, yolo_error = detect_student_id_area(
            yolo_model, pil_image, image_file, logger
        )
        if yolo_error:
            print(f"    ✗ 실패: {yolo_error}")
            return False
        print(f"    ✓ 완료 (신뢰도: {yolo_confidence:.3f})")
        
        # 3. OCR 인식
        print("  3. OCR 인식...")
        recognized_student_id, ocr_confidence = recognize_student_id_with_ocr(
            ocr_model, cropped_image, image_file, logger
        )
        print(f"    ✓ 완료 (학번: {recognized_student_id}, 신뢰도: {ocr_confidence:.3f})")
        
        # 4. 신뢰도 평가
        final_confidence = ocr_confidence if recognized_student_id else 0.0
        print("  4. 신뢰도 평가...")
        low_confidence_images = []
        is_success, low_confidence_images = handle_processing_result(
            recognized_student_id,
            final_confidence,
            image_file,
            test_path,
            pil_image,
            "테스트과목",
            extracted_path,
            low_confidence_images,
            logger
        )
        
        if is_success:
            print(f"    ✓ 성공 (최종 신뢰도: {final_confidence:.3f})")
        else:
            print(f"    ⚠ 낮은 신뢰도 (최종 신뢰도: {final_confidence:.3f})")
        
        print("\n✓ 전체 파이프라인 테스트 완료")
        return True
        
    except Exception as e:
        print(f"\n✗ 파이프라인 테스트 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """메인 함수 - 단계별 테스트 메뉴"""
    print("="*60)
    print("학번 인식 모듈 단계별 테스트")
    print("="*60)
    print("\n테스트할 단계를 선택하세요:")
    print("  1. 입력 검증 테스트")
    print("  2. 모델 로드 테스트")
    print("  3. 이미지 파일 수집 테스트")
    print("  4-1. 이미지 읽기 테스트")
    print("  4-2. YOLO 검출 테스트")
    print("  4-3. OCR 인식 테스트")
    print("  5. 단일 이미지 전체 파이프라인 테스트")
    print("  0. 모든 단계 순차 테스트")
    print("  q. 종료")
    
    choice = input("\n선택 (1-5, 0, q): ").strip()
    
    test_functions = {
        '1': test_step1_validation,
        '2': test_step2_model_loading,
        '3': test_step3_file_collection,
        '4-1': test_step4_image_reading,
        '4-2': test_step4_yolo_detection,
        '4-3': test_step4_ocr_recognition,
        '5': test_single_image_full_pipeline,
    }
    
    if choice == 'q':
        print("종료합니다.")
        return
    elif choice == '0':
        # 모든 단계 순차 테스트
        results = []
        for key, func in test_functions.items():
            try:
                result = func()
                results.append((key, result))
                if not result:
                    print(f"\n⚠ 단계 {key} 실패로 인해 중단합니다.")
                    break
            except KeyboardInterrupt:
                print("\n\n사용자에 의해 중단되었습니다.")
                return
            except Exception as e:
                print(f"\n✗ 단계 {key}에서 예외 발생: {e}")
                results.append((key, False))
                break
    elif choice in test_functions:
        try:
            test_functions[choice]()
        except KeyboardInterrupt:
            print("\n\n사용자에 의해 중단되었습니다.")
        except Exception as e:
            print(f"\n✗ 테스트 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("잘못된 선택입니다.")


if __name__ == '__main__':
    main()