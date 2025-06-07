# config.py로부터 import
from .config import (
    YOLO_MODEL_PATH, YOLO_CLASS_QN, YOLO_CLASS_ANS, 
    yolo_model, mnist_recognition_pipeline, KEY_PARSING_REGEX
)

from PIL import Image
import os

def test_mnist_pipeline():
    """MNIST 파이프라인을 테스트하는 함수"""
    
    # 입력 이미지 경로
    image_path = '/home/jdh251425/2025_DKU_Capstone/AI/신호및시스템-8/신호및시스템-8/신호및시스템-8_32201959.jpg'
    
    print(f"=== MNIST 파이프라인 테스트 ===")
    print(f"입력 이미지: {image_path}")
    
    # 파일 존재 여부 확인
    if not os.path.exists(image_path):
        print(f"❌ 오류: 파일이 존재하지 않습니다 - {image_path}")
        return
    
    try:
        # 이미지 로드
        print(f"📂 이미지 로딩 중...")
        image = Image.open(image_path)
        print(f"✅ 이미지 로드 성공: {image.size} (크기), {image.mode} (모드)")
        
        # 그레이스케일로 변환 (MNIST 모델용)
        if image.mode != 'L':
            print(f"🔄 그레이스케일로 변환 중... ({image.mode} → L)")
            image = image.convert('L')
        
        # MNIST 파이프라인 확인
        if mnist_recognition_pipeline is None:
            print(f"❌ 오류: MNIST 파이프라인이 로드되지 않았습니다")
            return
        
        print(f"🤖 MNIST 파이프라인 사용 가능")
        print(f"🔄 숫자 인식 수행 중...")
        
        # 예측 수행
        prediction = mnist_recognition_pipeline(image)
        
        print(f"\n=== 예측 결과 ===")
        if prediction:
            for i, pred in enumerate(prediction):
                label = pred.get('label', 'Unknown')
                score = pred.get('score', 0.0)
                print(type(score))
                print(f"순위 {i+1}: '{label}' (신뢰도: {score:.4f})")
        else:
            print(f"❌ 예측 결과가 없습니다")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mnist_pipeline()

