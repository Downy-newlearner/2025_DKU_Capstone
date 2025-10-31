## 예림, 유진이에게 - 다훈

객관식 답안은 항상 1개의 digit만 인식하면 되니까 MINST 모델을,
문제 번호는 여러개의 digits을 인식해야하니까 PaddleOCR을 사용하면 될 것 같아.(checkmate 로직을 사용해도 되겠지만 문제 번호는 항상 프린트되어있어서 PaddleOCR으로도 충분히 성능이 나올 것으로 예상)

그러니까 'checkmate/AI/answer_recognition/recognition/digit_recognizer.py' 코드를 집중적으로 보면 도움이 될꺼야. 예제 코드도 만들어놨으니까 확인해.

## 예제 코드 읽는 순서(digit_recognition_example_250924_dahun.py)

```
if __name__ == "__main__":
    # 실제 이미지 파일이 있는 경우
    # main()

    # 테스트 이미지로 실행
    test_with_sample_image()
```

이 부분부터 읽고 코드 따라가봐.

---

아래부터는 참고용이야.

---

## 🔄 전체 처리 순서 (Processing Pipeline)

답안지 인식은 다음 4단계로 진행됩니다:

**1단계: 전처리** → **2단계: 문제 번호 매핑** → **3단계: 개별 숫자 인식** → **4단계: 통합 처리**

```
원본 답안지 이미지
    ↓
[1] main.py - preprocess_answer_sheet()
    ├── YOLO로 문제/답안 영역 검출
    ├── 라인 검출로 문제별 분할
    └── 텍스트 영역 크롭 생성
    ↓
[2] recognition_of_question_number.py
    ├── 문제 번호와 y좌표 매핑
    └── 답안 키와 물리적 위치 연결
    ↓
[3] digit_recognizer.py
    ├── 개별 숫자 바운딩 박스 검출
    ├── MNIST 모델로 숫자 인식
    └── 거리 기반 숫자 그룹화(작성되어있는 숫자가 2, 5, 7이라면 문제에 대한 답 개수 정보를 반영해 그룹화를 한다. 예를들어 답 개수가 2개이고 2와 5가 5와 7보다 더 가깝다면 최종 인식 답은 [25, 7]이 된다.)
    ↓
[4] split_and_recognize_single_digits.py (선택적)
    ├── 디렉토리 전체 일괄 처리
    ├── 유클리드 거리 기반 고급 그룹화
    └── 최종 답안 조합 및 품질 검증
    ↓
최종 채점 결과 JSON
```

## 🔍 처리 순서별 모듈 상세

### 1단계: `main.py` - 전처리 및 통합 관리자

**목적**: 답안지 이미지 전처리 및 전체 파이프라인 관리

**핵심 함수들**:

- `preprocess_answer_sheet()`: **메인 전처리 함수**

  - **입력**: 원본 답안지 이미지 경로, 답안 키 데이터
  - **출력**: 문제별로 크롭된 텍스트 이미지 딕셔너리
  - **처리**: YOLO 검출 → 라인 분할 → 텍스트 크롭 생성

- `recognize_answer_sheet_data()`: **통합 인식 함수**
  - **입력**: 전처리된 크롭 이미지들, 답안 키, tail_counts
  - **출력**: `{'answer_json': {...}, 'failure_json': {...}}`
  - **처리**: 숫자 인식 → 그룹화 → 최종 답안 생성

### 2단계: `recognition_of_question_number.py` - 문제 번호 매핑

**목적**: 답안지의 물리적 위치(y좌표)와 문제 번호를 매핑

**핵심 함수**:

- `create_question_info_dict()`: 문제 번호와 y좌표 매핑 딕셔너리 생성
  - **입력**: 문제 번호 디렉토리 경로, 답안 키 JSON 파일 경로
  - **출력**: `{'1': [y_top, y_bottom], '2-1': [y_top, y_bottom]}` 형태의 매핑 딕셔너리

**처리 로직**:

- 답안 키에서 문제 번호 추출 (서브 문제 포함)
- 디렉토리명에서 y좌표 정보 파싱
- 문제 수와 좌표 수를 비교하여 자동 매핑

### 3단계: `digit_recognizer.py` - 기본 숫자 인식 엔진

**목적**: 답안지에서 개별 숫자를 분할하고 MNIST 모델로 인식

**핵심 함수들**:

- `pil_find_digit_contours_in_text_crop()`: 텍스트 영역에서 숫자 윤곽선 검출

  - **입력**: PIL 이미지, 최소 윤곽선 면적
  - **출력**: 숫자 바운딩 박스 리스트 `[(x, y, w, h), ...]`

- `pil_recognize_single_digit()`: 단일 숫자 이미지 인식

  - **입력**: 숫자 PIL 이미지
  - **출력**: `{'text': '3', 'confidence': 0.95}` 형태의 인식 결과

- `group_and_combine_digits()`: 인식된 숫자들을 의미있는 답안으로 그룹화
  - **입력**: 정렬된 숫자 리스트, 간격 임계값, 예상 답안 개수
  - **출력**: 결합된 답안 문자열 리스트 `['123', '45']`

### 4단계: `split_and_recognize_single_digits.py` - 고급 통합 인식 시스템

**목적**: 전처리된 답안 이미지들에서 개별 숫자를 인식하고 조합하여 최종 답안 추출

**핵심 함수들**:

- `generate_bounding_boxes_from_text_crop()`: 텍스트 크롭에서 숫자 바운딩 박스 생성

  - **입력**: 텍스트 크롭 이미지 경로
  - **출력**: 바운딩 박스 리스트 `[(x, y, w, h), ...]`

- `recognize_images_from_bounding_boxes()`: 바운딩 박스 내 숫자들을 MNIST 모델로 인식

  - **입력**: 이미지 경로, 바운딩 박스 리스트, 이미지 번호
  - **출력**: `{'status': 'success/failure', 'data': [((x,y), 'digit', img_idx), ...]}`

- `split_and_recognize_single_digits()`: **메인 함수** - 디렉토리 내 모든 답안 이미지 처리
  - **입력**: 답안 이미지 디렉토리 경로, 실패 로그 JSON 경로
  - **출력**: 원본 답안지별 인식 결과 딕셔너리
    ```python
    {
        "answer_paper_001": {
            "status": "success",
            "recognized_answers": [12, 3, 45]
        },
        "answer_paper_002": {
            "status": "failure",
            "reason": "Low confidence for digit recognition",
            "failed_crops": [{"path": "...", "reason": "..."}]
        }
    }
    ```

**고급 처리 로직**:

- 유클리드 거리 기반 숫자 그룹화
- 신뢰도 임계값(0.85) 기반 품질 검증
- 예상 답안 개수(`ac_N`)와 실제 인식 결과 매칭

## 💡 팀원 활용 가이드

**단일 이미지 처리**: `main.py`의 `preprocess_answer_sheet()` + `recognize_answer_sheet_data()` 조합 사용

**대량 이미지 처리**: `split_and_recognize_single_digits.py`의 메인 함수 직접 사용

**커스텀 숫자 인식**: `digit_recognizer.py`의 개별 함수들을 조합하여 사용
