# PaddleOCR-VL API 어댑터 가이드

## 현재 API 구조 분석

### 1. Frontend → Backend API 호출

**Frontend 기본 설정:**
- Base URL: `http://13.209.197.61:8080`
- 인증: Bearer Token 방식

**주요 API 엔드포인트:**
1. `/responses/upload-answer` (POST) - 답안지 업로드
2. `/update-id` (POST) - 학번 업데이트
3. `/exams` (POST) - 시험 정보 등록
4. `/images/{subject}/low-confidence` (GET) - 낮은 신뢰도 이미지 조회
5. `/responses` (PUT) - 답안 수정

### 2. Backend → AI Flask 서버 API 호출

**Backend 설정:**
- Flask 서버 URL: `${flask.server.url}` (application.properties에서 설정)

**현재 Flask API 엔드포인트:**
1. `/recognize/student_id` (POST) - 학번 인식
2. `/recognize/answer` (POST) - 답안 인식
3. `/get-student-image` (POST) - 학생 이미지 조회
4. `/generate-report` (POST) - 리포트 생성
5. `/health` (GET) - 헬스 체크

### 3. 현재 AI Flask 서버 구조

**주요 기능:**
- 학번 인식 (Student ID Recognition)
- 답안 인식 (Answer Recognition)
- 이미지 전처리 및 OCR
- Kafka를 통한 비동기 처리
- PDF 리포트 생성

## PaddleOCR-VL 교체를 위한 API 어댑터 설계

### 1. 유지해야 할 API 인터페이스

#### `/recognize/student_id` (POST)
```python
# 요청 형식
{
    "subject": "과목명",
    "answerSheetZip": "압축파일",
    "attendanceSheet": "출석부 엑셀파일"
}

# 응답 형식
{
    "status": "processing_started",
    "message": "Files received and student ID recognition process started in background.",
    "subject_folder": "과목폴더경로",
    "zip_folder_name": "압축해제폴더명"
}
```

#### `/recognize/answer` (POST)
```python
# 요청 형식
{
    "studentIdUpdateDto": {
        "subject": "과목명",
        "student_list": [
            {
                "file_name": "원본파일명_새파일명",
                "student_id": "학번"
            }
        ]
    },
    "examDto": {
        "subject": "과목명",
        "exam_date": "시험날짜",
        "questions": [
            {
                "question_number": 1,
                "sub_question_number": null,
                "question_type": "multiple_choice",
                "answer": "정답",
                "point": 점수
            }
        ]
    }
}

# 응답 형식
{
    "status": "processing_started",
    "message": "Answer recognition process started in background",
    "task_id": "작업ID",
    "subject": "과목명"
}
```

#### `/get-student-image` (POST)
```python
# 요청 형식
{
    "subject": "과목명",
    "student_id": "학번"
}

# 응답: 이미지 파일 (send_file)
```

### 2. PaddleOCR-VL 어댑터 구현 방향

#### A. 기존 Flask 구조 유지
```python
# app.py - 메인 Flask 애플리케이션
from paddle_ocr_adapter import PaddleOCRProcessor

@app.route('/recognize/student_id', methods=['POST'])
def recognize_student_id_endpoint():
    # 기존 인터페이스 유지
    # PaddleOCR-VL로 학번 인식 처리
    processor = PaddleOCRProcessor()
    return processor.process_student_id(request)

@app.route('/recognize/answer', methods=['POST'])
def recognize_answer_endpoint():
    # 기존 인터페이스 유지
    # PaddleOCR-VL로 답안 인식 처리
    processor = PaddleOCRProcessor()
    return processor.process_answers(request)
```

#### B. PaddleOCR-VL 프로세서 클래스
```python
# paddle_ocr_adapter.py
class PaddleOCRProcessor:
    def __init__(self):
        # PaddleOCR-VL 모델 초기화
        self.model = self.load_paddle_ocr_vl()
    
    def load_paddle_ocr_vl(self):
        # PaddleOCR-VL 모델 로드
        pass
    
    def process_student_id(self, request):
        # 학번 인식 로직
        # 1. 파일 업로드 처리
        # 2. PaddleOCR-VL로 학번 인식
        # 3. 결과 반환
        pass
    
    def process_answers(self, request):
        # 답안 인식 로직
        # 1. 이미지 전처리
        # 2. PaddleOCR-VL로 답안 인식
        # 3. 결과 반환
        pass
```

### 3. 데이터 흐름 유지

#### Kafka 메시지 형식 유지
```python
# 학번 인식 결과
{
    "subject": "과목명",
    "processing_folder": "처리폴더",
    "lowConfidenceImages": [
        {
            "student_id": "학번",
            "image_path": "이미지경로",
            "confidence": 신뢰도
        }
    ]
}

# 답안 인식 결과
{
    "student_id": "학번",
    "subject": "과목명",
    "answers": [
        {
            "question_number": 1,
            "sub_question_number": null,
            "student_answer": "학생답안",
            "confidence": 신뢰도
        }
    ]
}
```

### 4. 구현 단계

1. **PaddleOCR-VL 환경 설정**
   - 필요한 패키지 설치
   - 모델 다운로드 및 설정

2. **어댑터 클래스 구현**
   - 기존 인터페이스와 호환되는 어댑터 클래스
   - PaddleOCR-VL 모델 통합

3. **테스트 및 검증**
   - 기존 API 호출 테스트
   - 결과 형식 검증

4. **성능 최적화**
   - 배치 처리 최적화
   - 메모리 사용량 최적화

### 5. 설정 파일 업데이트

#### requirements.txt (새로 생성)
```
flask==2.3.3
paddlepaddle
paddleocr
kafka-python
pandas
opencv-python
numpy
pillow
reportlab
matplotlib
requests
```

#### config.py (새로 생성)
```python
# PaddleOCR-VL 설정
PADDLE_OCR_CONFIG = {
    'use_angle_cls': True,
    'lang': 'korean',
    'use_gpu': True,  # GPU 사용 여부
    'show_log': False
}

# Kafka 설정
KAFKA_CONFIG = {
    'bootstrap_servers': '43.202.183.74:9092',
    'topics': {
        'student_id': 'student-id-image-requests',
        'answers': 'student-responses',
        'low_confidence': 'low-confidence-images'
    }
}
```

이 가이드를 바탕으로 PaddleOCR-VL로 교체하면서도 기존 Backend와 Frontend의 API 호출 방식을 그대로 유지할 수 있습니다.
