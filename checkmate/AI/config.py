"""
Flask 애플리케이션 설정 파일

환경변수를 통해 설정을 오버라이드할 수 있습니다.
"""
import os

# ===== Kafka 설정 =====
KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', '15.164.7.162:9092')

# Kafka 토픽 설정
KAFKA_TOPICS = {
    'student_id_recognition_progress': os.getenv(
        'KAFKA_TOPIC_STUDENT_ID_RECOGNITION_PROGRESS',
        'student-id-recognition-progress'
    ),
    'student_id_image_requests': os.getenv(
        'KAFKA_TOPIC_STUDENT_ID_IMAGE_REQUESTS',
        'student-id-image-requests'
    ),
    'student_responses': os.getenv(
        'KAFKA_TOPIC_STUDENT_RESPONSES',
        'student-responses'
    ),
    'low_confidence_images': os.getenv(
        'KAFKA_TOPIC_LOW_CONFIDENCE_IMAGES',
        'low-confidence-images'
    ),
}

# ===== Flask 설정 =====
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# ===== 파일 업로드 설정 =====
UPLOAD_FOLDER_BASE = os.getenv(
    'UPLOAD_FOLDER_BASE',
    os.path.join(os.path.expanduser('~'), 'ocr_flask_uploads')
)

# ===== Spring 서버 설정 =====
SPRING_CALLBACK_PATH = os.getenv('SPRING_CALLBACK_PATH', '/api/ocr/callback')
SPRING_CALLBACK_TIMEOUT = int(os.getenv('SPRING_CALLBACK_TIMEOUT', '10'))

# ===== 이미지 파일 확장자 =====
ALLOWED_EXTENSIONS_ZIP = {'zip'}
ALLOWED_EXTENSIONS_XLSX = {'xlsx'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}

