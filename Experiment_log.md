# 학번 인식 모델 실험 로그

## 실험 목적
`인공지능 중간고사 2023` 이미지 세트(16장)를 사용하여 YOLO + OCR 기반 학번 인식 파이프라인의 성능을 평가하고, 실제 운영 환경에서의 동작을 검증합니다.

## 실험 환경
- **테스트 데이터**: `/home/jdh251425/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/Data/인공지능 중간고사 2023`
- **이미지 수**: 16장
- **모델**: YOLOv8 (학번 영역 검출) + PaddleOCR (학번 인식)
- **실행 환경**: CPU 모드 (CUDA 호환성 문제로 인해)
- **실행 스크립트**: `student_id_recognition/main.py`

## 실험 계획

### 1단계: 사전 준비 및 문제 해결
- [x] CUDA 호환성 문제 해결 (CPU 모드 강제 설정)
- [x] PaddleOCR API 호환성 문제 해결 (cls 파라미터 처리)
- [x] 예외 처리 강화
- [x] 로깅 설정 확인

### 2단계: 모델 로드 및 검증
- YOLO 모델 로드 확인
- OCR 모델 초기화 확인
- 모델 경로 검증

### 3단계: 이미지 처리 실행
- 16개 이미지 순차 처리
- 각 단계별 성공/실패 로깅
- 중간 결과 저장

### 4단계: 결과 분석
- YOLO 검출 성공률
- OCR 인식 성공률
- 최종 신뢰도 통과율
- 파일명 변경 성공률
- lowConfidenceImages 분석

## 예상 결과
- **YOLO 검출 성공률**: 100% (테스트 결과 기반)
- **OCR 인식 성공률**: 50-75% (예상)
- **최종 신뢰도 통과율**: 31-63% (OCR 성능에 의존)
- **lowConfidenceImages**: 6-11개 (38-69%)

## 발생 가능한 문제 및 대응 방안

### 문제 1: CUDA 호환성 오류
**증상**: `CUDA error: no kernel image is available for execution on the device`
**원인**: GPU가 CUDA capability 6.1 (TITAN Xp)인데 PyTorch가 7.0+만 지원
**해결**: CPU 모드로 강제 실행

### 문제 2: PaddleOCR API 변경
**증상**: `TypeError: ocr() got an unexpected keyword argument 'cls'`
**원인**: PaddleOCR 버전에 따라 API 변경
**해결**: try-except로 fallback 처리

### 문제 3: OCR 인식 실패
**증상**: 학번 추출 실패 또는 낮은 신뢰도
**원인**: 이미지 품질, 크롭 영역 정확도
**해결**: 낮은 신뢰도 이미지는 Base64로 저장하여 수동 검토

### 문제 4: 메모리 부족
**증상**: 메모리 오류 발생
**원인**: Base64 인코딩으로 메모리 사용량 증가
**해결**: 주기적 가비지 컬렉션, 이미지 처리 후 즉시 삭제

### 문제 5: 파일명 변경 충돌
**증상**: 동일 학번으로 인한 파일명 충돌
**원인**: 여러 이미지에 동일 학번
**해결**: `get_unique_filename()` 함수로 자동 해결

## 사전 문제 해결 완료 사항

### ✅ 1. CUDA 호환성 문제 해결
- `main()` 함수 시작 부분에 CPU 모드 강제 설정 추가
- `get_yolo_model()` 함수에서 CPU 모드 설정
- YOLO 추론 시 `device='cpu'` 파라미터 추가

### ✅ 2. PaddleOCR API 호환성 문제 해결
- `ocr()` 메서드의 `cls` 파라미터 오류 처리
- `predict()` 메서드 지원 (최신 API)
- 파일 경로 기반 OCR fallback 추가

### ✅ 3. 예외 처리 강화
- OCR 결과 파싱 시 다양한 형식 지원
- 각 단계별 예외 처리 및 로깅

### ✅ 4. 메모리 관리
- 이미지 처리 후 즉시 메모리 해제
- 주기적 가비지 컬렉션 (50개마다)

## 실행 전 체크리스트

- [ ] 모델 파일 존재 확인: `student_id_recognition/model/best_student_id.pt`
- [ ] 테스트 이미지 디렉토리 확인: `Data/인공지능 중간고사 2023`
- [ ] 필요한 라이브러리 설치 확인 (ultralytics, paddleocr, opencv-python)
- [ ] 디스크 공간 확인 (Base64 인코딩으로 인한 메모리 사용)
- [ ] 실행 권한 확인

## 실험 실행 기록

