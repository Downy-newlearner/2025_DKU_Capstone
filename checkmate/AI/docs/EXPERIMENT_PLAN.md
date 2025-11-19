# 학번 인식 실험 계획서

## 실험 개요

**목적**: `인공지능 중간고사 2023` 이미지 세트를 사용하여 YOLO + OCR 기반 학번 인식 파이프라인의 실제 성능을 평가하고 검증합니다.

**대상 데이터**: 16장의 학생 답안지 이미지

**실행 스크립트**: `student_id_recognition/main.py`

## 실험 환경

### 하드웨어
- CPU: 사용 가능
- GPU: TITAN Xp (CUDA capability 6.1) - 호환성 문제로 CPU 모드 사용

### 소프트웨어
- Python 3.13.2
- YOLOv8 (Ultralytics)
- PaddleOCR
- OpenCV

### 데이터
- 경로: `/home/jdh251425/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/Data/인공지능 중간고사 2023`
- 이미지 수: 16장
- 평균 파일 크기: ~900KB

## 실험 단계

### Phase 1: 사전 준비 (완료)
1. ✅ CUDA 호환성 문제 해결
2. ✅ PaddleOCR API 호환성 문제 해결
3. ✅ 예외 처리 강화
4. ✅ 로깅 설정

### Phase 2: 모델 로드 및 검증
- YOLO 모델 로드 확인
- OCR 모델 초기화 확인
- 모델 경로 검증

### Phase 3: 이미지 처리 실행
- 16개 이미지 순차 처리
- 각 단계별 성공/실패 로깅
- 중간 결과 저장

### Phase 4: 결과 분석
- YOLO 검출 성공률 측정
- OCR 인식 성공률 측정
- 최종 신뢰도 통과율 계산
- 파일명 변경 성공률 확인
- lowConfidenceImages 분석

## 예상 결과

### 성공 지표
- **YOLO 검출 성공률**: 100% (테스트 결과 기반)
- **OCR 인식 성공률**: 50-75% (예상)
- **최종 신뢰도 통과율**: 31-63% (OCR 성능에 의존)
- **파일명 변경 성공**: 5-10개 (31-63%)

### 실패 케이스 예상
- **lowConfidenceImages**: 6-11개 (38-69%)
- 주요 원인:
  - OCR 신뢰도 낮음 (< 0.5)
  - 8자리 학번 추출 실패
  - 최종 신뢰도 < 0.8 임계값

## 발생 가능한 문제 및 대응 방안

### 문제 1: CUDA 호환성 오류 ✅ 해결됨
**증상**: `CUDA error: no kernel image is available for execution on the device`
**원인**: GPU가 CUDA capability 6.1인데 PyTorch가 7.0+만 지원
**해결**: CPU 모드로 강제 실행 (환경 변수 설정)

### 문제 2: PaddleOCR API 변경 ✅ 해결됨
**증상**: `TypeError: ocr() got an unexpected keyword argument 'cls'`
**원인**: PaddleOCR 버전에 따라 API 변경
**해결**: try-except로 fallback 처리, predict() 메서드 지원

### 문제 3: OCR 인식 실패 ⚠️ 예상됨
**증상**: 학번 추출 실패 또는 낮은 신뢰도
**원인**: 이미지 품질, 크롭 영역 정확도
**대응**: 낮은 신뢰도 이미지는 Base64로 저장하여 수동 검토

### 문제 4: 메모리 부족 ⚠️ 모니터링 필요
**증상**: 메모리 오류 발생
**원인**: Base64 인코딩으로 메모리 사용량 증가 (16개 × ~1MB = ~16MB)
**대응**: 주기적 가비지 컬렉션, 이미지 처리 후 즉시 삭제

### 문제 5: 파일명 변경 충돌 ✅ 해결됨
**증상**: 동일 학번으로 인한 파일명 충돌
**원인**: 여러 이미지에 동일 학번
**해결**: `get_unique_filename()` 함수로 자동 해결

### 문제 6: 이미지 읽기 실패 ⚠️ 예외 처리됨
**증상**: PIL Image.open() 실패
**원인**: 손상된 이미지 파일
**대응**: 예외 처리 후 Base64 fallback 사용

## 실행 방법

### 기본 실행
```python
from student_id_recognition.main import main

result = main(
    extracted_images_path="/path/to/인공지능 중간고사 2023",
    student_numbers_from_xlsx=[],  # 빈 리스트 또는 학번 리스트
    subject_name="인공지능 중간고사 2023",
    producer=None,  # Kafka 없이 실행
    student_id_recognition_topic="",
    task_identifier="test_001"
)

print(f"처리 완료: {len(result['lowConfidenceImages'])}개 낮은 신뢰도 이미지")
```

### 결과 확인
- 성공한 이미지: 파일명이 `{과목명}_{학번}.jpg`로 변경됨
- 실패한 이미지: `lowConfidenceImages` 리스트에 Base64 인코딩되어 포함
- 디버그 JSON: `student_id_recognition_debug.json` 파일 생성

## 평가 기준

### 성공 기준
1. **YOLO 검출**: 학번 영역 검출 성공 (신뢰도 > 0.3)
2. **OCR 인식**: 8자리 학번 추출 성공
3. **최종 신뢰도**: ≥ 0.8 (YOLO 0.6 + OCR 0.4 가중 평균)

### 실패 기준
1. YOLO 검출 실패
2. OCR 인식 실패 또는 신뢰도 낮음
3. 8자리 학번 추출 실패
4. 최종 신뢰도 < 0.8

## 결과 분석 항목

1. **전체 처리 통계**
   - 처리된 이미지 수
   - 성공/실패 비율
   - 평균 처리 시간

2. **YOLO 성능**
   - 검출 성공률
   - 평균 신뢰도
   - 검출된 박스 수

3. **OCR 성능**
   - 인식 성공률
   - 평균 신뢰도
   - 학번 추출 성공률

4. **최종 성능**
   - 신뢰도 통과율
   - 파일명 변경 성공률
   - lowConfidenceImages 분석

## 후속 작업

1. 실패한 이미지 수동 검토
2. OCR 성능 개선 방안 검토
3. 신뢰도 임계값 조정 검토
4. 추가 전처리 기법 적용 검토

