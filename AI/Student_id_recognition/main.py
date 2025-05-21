import json
from AI.Student_id_recognition.student_num_comparision.student_num_comparision import student_num_comparision
from AI.Student_id_recognition.extract_student_num.extract_student_num import extract_student_num
import os

# 예시: 과목명, 어트리뷰트, 학번 리스트가 담긴 JSON 불러오기
def load_json(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def make_json(answer_sheet_dir_path):
    # 디렉토리명(과목명) 추출
    subject = os.path.basename(os.path.normpath(answer_sheet_dir_path))
    # JSON 구조 생성
    data = {
        "subject": subject,
        "student_list": [],
        "base64_data": []
    }
    return data

# 유식 함수 예시 (답안지에서 학번 추출)
def extract_student_num(answer_sheet_img_path: str) -> int:
    # 실제 구현에서는 이미지에서 학번을 추출하는 코드가 들어감

    return -1

# 메인 처리 함수
def main(answer_sheet_dir_path):
    data = make_json(answer_sheet_dir_path)
    student_num_list = []  # 기존 학번 리스트가 있다면 여기에 할당

    for root, dirs, files in os.walk(answer_sheet_dir_path):
        for file in files:
            answer_sheet = os.path.join(root, file)
            # 1. 답안지에서 학번 추출
            student_num = extract_student_num(answer_sheet)
            # 2. 학번 비교 (다훈 함수)
            go_to_json = student_num_comparision(student_num, student_num_list)
            # 3. 조건에 따라 결과 저장
            if go_to_json:
                with open(answer_sheet, 'rb') as img_file:
                    import base64
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                data['student_list'].append(str(student_num))
                data['base64_data'].append(img_base64)
    return data

# 예시 실행 코드
if __name__ == '__main__':
    answer_sheet_dir_path = './Mathematics'  # 예시 디렉토리명
    result_json = main(answer_sheet_dir_path)
    print(json.dumps(result_json, ensure_ascii=False, indent=2))
