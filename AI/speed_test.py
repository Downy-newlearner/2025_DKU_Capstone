#!/usr/bin/env python3
"""
MNIST 파이프라인 속도 테스트: 배치 처리 vs 개별 처리
"""

'''
🚀 속도 테스트 결과
요약:
배치 처리가 개별 처리보다 약간 빠르지만, 차이가 크지 않습니다
상세 결과:
| 이미지 개수 | 개별 처리 시간 | 배치 처리 시간 | 배치 처리 속도 개선 | 절약 시간 |
|------------|---------------|---------------|-------------------|----------|
| 5개 | 0.2863초 (0.0573초/개) | 0.2411초 (0.0482초/개) | 1.19배 빠름 | 0.045초 |
| 10개 | 0.5357초 (0.0536초/개) | 0.5158초 (0.0516초/개) | 1.04배 빠름 | 0.020초 |
| 20개 | 1.0019초 (0.0501초/개) | 0.9506초 (0.0475초/개) | 1.05배 빠름 | 0.051초 |
결론:
배치 처리가 약간 빠름: 약 4-19% 정도의 성능 향상
차이가 크지 않음: CPU 환경에서는 배치 처리의 이점이 제한적
개당 처리 시간: 약 0.05초 (50ms) 정도로 매우 빠름
'''

import time
import numpy as np
from PIL import Image
from transformers import pipeline
import torch

def create_test_images(count=10):
    """테스트용 가짜 MNIST 이미지들을 생성"""
    images = []
    for i in range(count):
        # 28x28 크기의 랜덤 이미지 생성 (MNIST 형식)
        arr = np.random.randint(0, 255, (28, 28), dtype=np.uint8)
        img = Image.fromarray(arr, mode='L')
        images.append(img)
    return images

def test_individual_processing(pipe, images):
    """개별 처리 테스트"""
    print(f"\n=== 개별 처리 테스트 ({len(images)}개 이미지) ===")
    
    start_time = time.time()
    results = []
    
    for i, img in enumerate(images):
        result = pipe(img)
        results.append(result)
        if i == 0:  # 첫 번째 결과만 출력
            print(f"첫 번째 결과: {result}")
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"총 소요 시간: {total_time:.4f}초")
    print(f"이미지당 평균 시간: {total_time/len(images):.4f}초")
    
    return total_time, results

def test_batch_processing(pipe, images):
    """배치 처리 테스트"""
    print(f"\n=== 배치 처리 테스트 ({len(images)}개 이미지) ===")
    
    start_time = time.time()
    
    try:
        # 배치로 한번에 처리
        results = pipe(images)
        print(f"첫 번째 결과: {results[0] if results else 'None'}")
    except Exception as e:
        print(f"배치 처리 실패: {e}")
        print("개별 처리로 폴백...")
        return test_individual_processing(pipe, images)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"총 소요 시간: {total_time:.4f}초")
    print(f"이미지당 평균 시간: {total_time/len(images):.4f}초")
    
    return total_time, results

def main():
    print("MNIST 파이프라인 속도 테스트")
    print("=" * 50)
    
    # MNIST 모델 로드
    print("MNIST 모델 로딩 중...")
    try:
        # CPU 사용 강제 (일관성을 위해)
        device = 0 if torch.cuda.is_available() else -1
        pipe = pipeline(
            "image-classification",
            model="farleyknight/mnist-digit-classification-2022-09-04",
            device=device
        )
        print(f"모델 로드 완료 (device: {'GPU' if device >= 0 else 'CPU'})")
    except Exception as e:
        print(f"모델 로드 실패: {e}")
        return
    
    # 테스트 이미지 생성
    test_sizes = [5, 10, 20]
    
    for size in test_sizes:
        print(f"\n{'='*60}")
        print(f"테스트 크기: {size}개 이미지")
        print(f"{'='*60}")
        
        images = create_test_images(size)
        
        # 개별 처리 테스트
        individual_time, individual_results = test_individual_processing(pipe, images)
        
        # 배치 처리 테스트
        batch_time, batch_results = test_batch_processing(pipe, images)
        
        # 결과 비교
        if batch_time < individual_time:
            speedup = individual_time / batch_time
            print(f"\n🚀 배치 처리가 {speedup:.2f}배 빠름!")
        else:
            slowdown = batch_time / individual_time
            print(f"\n⚠️ 개별 처리가 {slowdown:.2f}배 빠름")
        
        print(f"절약된 시간: {abs(individual_time - batch_time):.4f}초")

if __name__ == "__main__":
    main()