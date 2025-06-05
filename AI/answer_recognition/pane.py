'''
recognize_answer_sheet_data 함수의 입력 매개변수 설명:

1. processed_ans_crops (Dict[str, Image.Image]):
   - 타입: 딕셔너리 (str을 키로, PIL Image 객체를 값으로 가짐)
   - 설명: 전처리 단계에서 생성된 개별 답안 텍스트 조각 이미지들의 컬렉션입니다.
     각 키는 해당 텍스트 조각의 고유 식별자 (예: "과목명_학번_L라인번호_x좌표_qn문제번호_ac답개수")이며,
     값은 해당 텍스트 조각의 PIL Image 객체입니다.
   - 예시 키: "Math_32174515_LL0_x100_qn1-1_ac1"

2. answer_key_data (Dict[str, Any]):
   - 타입: 딕셔너리
   - 설명: 원본 답안지 키 JSON 파일 (예: test_answer.json)에서 로드된 전체 데이터입니다.
     주로 문제 번호, 하위 문제 번호, 문제 유형, 정답, 배점, 그리고 각 문제에 대한 예상 답안 개수(answer_count) 등의 정보를 포함합니다.
     현재 함수 로직에서는 직접적으로 모든 정보를 사용하고 있지는 않지만, 키 파싱을 통해 추출된 'expected_answer_count' (ac_val)가 
     이 데이터의 'answer_count'에서 비롯된 정보입니다. 향후 다른 정보도 활용될 가능성이 있습니다.
   - 주요 포함 정보: "questions" 리스트 (각 문제의 상세 정보 포함)
'''

'''
recognize_answer_sheet_data 함수의 반환값 설명:

- 타입: Dict[str, Any]
- 구조:
{
  "answer_json": {
    "subject": "math",
    "studentAnswersList": [
      {
        "student_id": "student001",
        "answers": [
          {
            "question_number": 1,
            "sub_question_number": 1,
            "student_answer": "A"
          },
          {
            "question_number": 1,
            "sub_question_number": 2,
            "student_answer": "B"
          }
        ]
      },
      {
        "student_id": "student002",
        "answers": [
          {
            "question_number": 2,
            "sub_question_number": 1,
            "student_answer": "C"
          },
          {
            "question_number": 2,
            "sub_question_number": 2,
            "student_answer": "D"
          }
        ]
      }
    ]
  },

  "failure_json": {
    "subject": "english",
    "images": [
      {
        "student_id": "student001",
        "file_name": "student001_q1_1.jpg",
        "base64_data": "iVBORw0KGgoAAAANSUhEUgAAA... (생략)",
        "question_number": 1,
        "sub_question_number": 1
      },
      {
        "student_id": "student002",
        "file_name": "student002_q2_1.jpg",
        "base64_data": "iVBORw0KGgoAAAANSUhEUgAAA... (생략)",
        "question_number": 2,
        "sub_question_number": 1
      }
    ]
  }
}


⸻

	•	설명:
recognize_answer_sheet_data 함수는 최종적으로 두 개의 주요 키 "answer_json"과 "failure_json"을 포함하는 Dict[str, Any] 타입의 딕셔너리를 반환합니다.
"answer_json"은 인식에 성공한 학생별 정답 데이터를 포함하고, "failure_json"은 인식에 실패한 이미지 정보를 포함합니다.
현재 두 JSON 형식은 Flask에서 Spring으로 데이터를 전송하기 위한 최종 출력 포맷으로, Spring DTO 구조와 일치하도록 구성되어 있습니다.
	•	“answer_json”의 반환 형식 예시:

{
  "subject": "math",
  "studentAnswersList": [
    {
      "student_id": "student001",
      "answers": [
        {
          "question_number": 1,
          "sub_question_number": 1,
          "student_answer": "A"
        },
        {
          "question_number": 1,
          "sub_question_number": 2,
          "student_answer": "B"
        }
      ]
    },
    {
      "student_id": "student002",
      "answers": [
        {
          "question_number": 2,
          "sub_question_number": 1,
          "student_answer": "C"
        },
        {
          "question_number": 2,
          "sub_question_number": 2,
          "student_answer": "D"
        }
      ]
    }
  ]
}

	•	“failure_json”의 반환 형식 예시:

{
  "subject": "english",
  "images": [
    {
      "student_id": "student001",
      "file_name": "student001_q1_1.jpg",
      "base64_data": "iVBORw0KGgoAAAANSUhEUgAAA... (생략)",
      "question_number": 1,
      "sub_question_number": 1
    },
    {
      "student_id": "student002",
      "file_name": "student002_q2_1.jpg",
      "base64_data": "iVBORw0KGgoAAAANSUhEUgAAA... (생략)",
      "question_number": 2,
      "sub_question_number": 1
    }
  ]
}

위 형식은 실제 서비스 연동을 위한 확정된 포맷이며, 이후 로직 변경이나 필드 추가가 필요할 경우 Spring DTO 정의에 따라 반영될 수 있습니다.

'''

from PIL import Image
from pathlib import Path

# --- 테스트용 Dummy 데이터 정의 ---
subject_student_id_base = "신호및시스템_20240101"

ans_text_crop_full_info = {
    "y_in_line_relative_to_line_crop_top": 15,
    "line_y_top_relative_to_ans_area": 100,
    "ans_area_y_offset_orig": 1000,
    "x_in_line": 200,
    "line_id_in_ans_area": "1",
    "image_obj": Image.new("RGB", (50, 20))  # 50x20 크기의 dummy 이미지
}

# 예: 실제 위치가 1000 + 100 + 15 + 10 = 1125쯤 되는 곳이면...
question_info_dict = {
    "2-1": [1100, 1130],  # y 중심 좌표 1125가 이 범위에 포함
    "2-2": [1140, 1170]
}

# 실제 test_answer_json에서 가져온 일부
answer_key_data = {
    "questions": [
        {
            "question_number": 2,
            "sub_question_number": 1,
            "answer": "8",
            "allocated_score": 5,
            "answer_count": 1
        },
        {
            "question_number": 2,
            "sub_question_number": 2,
            "answer": "6",
            "allocated_score": 5,
            "answer_count": 1
        }
    ]
}

# --- 테스트 함수 정의 (이전 함수 그대로 사용) ---
def generate_final_key_for_ans_crop(
    subject_student_id_base: str,
    ans_text_crop_full_info: dict,
    question_info_dict: dict,
    answer_key_data: dict
) -> str:
    y_in_line = ans_text_crop_full_info['y_in_line_relative_to_line_crop_top']
    line_y_top = ans_text_crop_full_info['line_y_top_relative_to_ans_area']
    ans_area_y_offset = ans_text_crop_full_info['ans_area_y_offset_orig']
    text_crop_height = ans_text_crop_full_info['image_obj'].height
    abs_y_top_of_text_crop = ans_area_y_offset + line_y_top + y_in_line
    abs_y_center_of_text_crop = line_y_top + (text_crop_height // 2)

    matching_qn_str = "unknownQN"
    for qn_key, y_range_orig in question_info_dict.items():
        if y_range_orig[0] <= abs_y_center_of_text_crop <= y_range_orig[1]:
            matching_qn_str = qn_key
            break

    answer_count_for_qn = 0
    for q_entry in answer_key_data.get('questions', []):
        qn_str_key = str(q_entry.get('question_number'))
        sub_qn_val = q_entry.get('sub_question_number', 0)
        sub_qn_str_key = str(sub_qn_val) if sub_qn_val and str(sub_qn_val) != "0" else ""
        current_key_in_answer_data = f"{qn_str_key}-{sub_qn_str_key}" if sub_qn_str_key else qn_str_key
        if current_key_in_answer_data == matching_qn_str:
            answer_count_for_qn = q_entry.get('answer_count', 0)
            break

    x_in_line_coord = ans_text_crop_full_info['x_in_line']
    line_id_in_ans_area = ans_text_crop_full_info.get('line_id_in_ans_area','lineX')

    key_base = f"{subject_student_id_base}_L{line_id_in_ans_area}_x{x_in_line_coord}_y{abs_y_top_of_text_crop}_qn{matching_qn_str}_ac{answer_count_for_qn}"


      # 현재 중심 좌  표 확인
    print(f"[디버그] abs_y_center_of_text_crop: {abs_y_center_of_text_crop}")

    # 범위 확인
    for qn_key, y_range_orig in question_info_dict.items():
        print(f"[디버그] checking {qn_key}: {y_range_orig} vs {abs_y_center_of_text_crop}")
        
    return key_base.replace(" ", "")



# --- 실행 및 결과 출력 ---
final_key = generate_final_key_for_ans_crop(
    subject_student_id_base,
    ans_text_crop_full_info,
    question_info_dict,
    answer_key_data
)

print("[Test Result] 최종 Key 생성 결과:")
print(final_key)

