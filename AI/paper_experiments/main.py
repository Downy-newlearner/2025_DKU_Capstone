"""
OCR 성능 비교 실험 - 메인 실행 파일

1. YOLO로 답안 영역 추출 (Phase 1)
2. EasyOCR 기준선 실험 및 시각화 (Phase 2) 
3. 3단계 전처리 파이프라인 + MNIST 분류 실험 (Phase 3)
"""

import argparse
from pathlib import Path

from config import ORIGINAL_IMAGES_DIR, RESULTS_DIR
from yolo_extractor import YOLOAnswerExtractor
from easyocr_baseline import EasyOCRBaseline
from preprocessing_pipeline import PreprocessingPipeline


def create_sample_directories():
    """필요한 디렉토리 구조 생성"""
    directories = [
        ORIGINAL_IMAGES_DIR,
        RESULTS_DIR,
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"📁 디렉토리 생성: {directory}")


def run_phase1_yolo_extraction():
    """Phase 1: YOLO를 사용한 답안 영역 추출"""
    print("\n" + "🚀" * 20)
    print("PHASE 1: YOLO 답안 영역 추출")
    print("🚀" * 20)
    
    extractor = YOLOAnswerExtractor()
    extracted_paths = extractor.extract_all_answer_areas()
    
    if not extracted_paths:
        print("❌ 답안 영역 추출 실패. Phase 2, 3을 진행할 수 없습니다.")
        return False
    
    print(f"✅ Phase 1 완료: {len(extracted_paths)}개 답안 영역 추출")
    return True


def run_phase2_easyocr_baseline():
    """Phase 2: EasyOCR 기준선 실험"""
    print("\n" + "📖" * 20)
    print("PHASE 2: EasyOCR 기준선 실험")
    print("📖" * 20)
    
    baseline = EasyOCRBaseline()
    results = baseline.run_baseline_experiment()
    
    if not results:
        print("❌ EasyOCR 실험 실패.")
        return False
    
    successful_results = [r for r in results if r.get("success", False)]
    print(f"✅ Phase 2 완료: {len(successful_results)}/{len(results)}개 이미지 처리 성공")
    return True


def run_phase3_preprocessing_pipeline():
    """Phase 3: 3단계 전처리 파이프라인 + MNIST 분류 실험"""
    print("\n" + "🔧" * 20)
    print("PHASE 3: 3단계 전처리 파이프라인 + MNIST 분류")
    print("🔧" * 20)
    
    pipeline = PreprocessingPipeline()
    results = pipeline.run_pipeline_experiment()
    
    if not results:
        print("❌ 전처리 파이프라인 실험 실패.")
        return False
    
    successful_results = [r for r in results if r.get("success", False)]
    print(f"✅ Phase 3 완료: {len(successful_results)}/{len(results)}개 이미지 처리 성공")
    return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="OCR 성능 비교 실험")
    parser.add_argument(
        "--phase", 
        type=int, 
        choices=[1, 2, 3], 
        help="실행할 단계 (1: YOLO 추출, 2: EasyOCR 실험, 3: 전처리 파이프라인)"
    )
    parser.add_argument(
        "--setup", 
        action="store_true", 
        help="디렉토리 구조 생성"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("OCR 성능 비교 실험 시작")
    print("=" * 60)
    
    # 디렉토리 구조 생성
    if args.setup:
        create_sample_directories()
        print(f"\n✅ 디렉토리 구조 생성 완료!")
        print(f"📂 원본 이미지를 다음 폴더에 넣어주세요: {ORIGINAL_IMAGES_DIR}")
        return
    
    # 개별 단계 실행
    if args.phase == 1:
        success = run_phase1_yolo_extraction()
        if success:
            print(f"\n🎉 Phase 1 완료! 다음 명령어로 Phase 2를 실행하세요:")
            print(f"python main.py --phase 2")
        return
    
    elif args.phase == 2:
        success = run_phase2_easyocr_baseline()
        if success:
            print(f"\n🎉 Phase 2 완료! 다음 명령어로 Phase 3을 실행하세요:")
            print(f"python main.py --phase 3")
        return
    
    elif args.phase == 3:
        success = run_phase3_preprocessing_pipeline()
        if success:
            print(f"\n🎉 Phase 3 완료! 모든 실험이 완료되었습니다.")
        return
    
    # 전체 실험 실행 (기본값)
    print("🔄 전체 실험 실행 중...")
    
    # Phase 1: YOLO 답안 영역 추출
    phase1_success = run_phase1_yolo_extraction()
    if not phase1_success:
        print("❌ 전체 실험 중단: Phase 1 실패")
        return
    
    # Phase 2: EasyOCR 기준선 실험
    phase2_success = run_phase2_easyocr_baseline()
    if not phase2_success:
        print("❌ 전체 실험 중단: Phase 2 실패")
        return
    
    # Phase 3: 3단계 전처리 파이프라인 실험
    phase3_success = run_phase3_preprocessing_pipeline()
    if not phase3_success:
        print("❌ 전체 실험 중단: Phase 3 실패")
        return
    
    # 전체 결과 요약
    print("\n" + "🎉" * 20)
    print("전체 실험 완료!")
    print("🎉" * 20)
    print(f"📂 결과 위치: {RESULTS_DIR}")
    print(f"   📊 Phase 1 - 답안 이미지: {RESULTS_DIR}/yolo_answer_images/")
    print(f"   📊 Phase 2 - EasyOCR 결과: {RESULTS_DIR}/easyocr_results/")
    print(f"   📊 Phase 2 - EasyOCR 시각화: {RESULTS_DIR}/visualizations/")
    print(f"   📊 Phase 3 - 파이프라인 결과: {RESULTS_DIR}/pipeline_results/")
    print(f"   📊 Phase 3 - 파이프라인 시각화: {RESULTS_DIR}/pipeline_visualizations/")
    
    print(f"\n📈 성능 비교:")
    print(f"   방법 1: EasyOCR 단독 사용 → {RESULTS_DIR}/easyocr_results/")
    print(f"   방법 2: 3단계 전처리 파이프라인 + MNIST → {RESULTS_DIR}/pipeline_results/")


if __name__ == "__main__":
    main() 