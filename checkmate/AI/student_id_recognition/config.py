"""
학번 인식 모듈의 설정 및 상수 정의
"""
import os
import re

# ===== 경로 설정 =====
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'model')
YOLO_MODEL_PATH = os.path.join(MODEL_DIR, 'best_student_id.pt')

# ===== YOLO 설정 =====
STUDENT_ID_CLASS_ID = 0  # 학번 영역 클래스 ID (args_student_id.yaml 확인 필요)
YOLO_CONF_THRESHOLD = 0.25  # YOLO 신뢰도 임계값 (args_student_id.yaml: conf: 0.22)

# ===== OCR 설정 =====
OCR_USE_GPU = False  # 또는 True
OCR_LANG = 'en'  # 숫자만 인식 (영어 모델이 숫자 인식에 적합)

# ===== 신뢰도 설정 =====
CONFIDENCE_THRESHOLD = 0.8  # 최종 신뢰도 임계값

# ===== 이미지 파일 확장자 =====
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# ===== 학번 정규식 =====
STUDENT_ID_PATTERN = re.compile(r'\d{8}')

