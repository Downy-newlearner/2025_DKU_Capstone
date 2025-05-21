import json
from AI.Student_id_recognition.student_num_comparision.student_num_comparision import student_num_comparision
from AI.Student_id_recognition.extract_student_num.extract_student_num import extract_student_num
import os


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

# 메인 처리 함수
def main(answer_sheet_dir_path):
    data = make_json(answer_sheet_dir_path)
    student_num_list = []  # 기존 학번 리스트가 있다면 여기에 할당

    for root, dirs, files in os.walk(answer_sheet_dir_path):
        for file in files:
            answer_sheet = os.path.join(root, file)
            # 1. 답안지에서 학번 추출
            student_num = extract_student_num(answer_sheet) # 여기만 수정해주면 돼!!!!! 0521 18:13 정다훈
            # 2. 학번 비교 (다훈 함수)
            go_to_json = student_num_comparision(student_num, student_num_list)
            # 3. 조건에 따라 결과 저장
            if go_to_json:
                with open(answer_sheet, 'rb') as img_file:
                    import base64
                    img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                data['student_list'].append(str(student_num))
                data['base64_data'].append(img_base64)
                continue
            
            elif go_to_json == False:
                new_file_name = f"{student_num}.jpg"
                new_file_path = os.path.join(root, new_file_name)
                os.rename(answer_sheet, new_file_path)
    
    return data

# 예시 실행 코드
if __name__ == '__main__':
    answer_sheet_dir_path = './Mathematics'  # 예시 디렉토리명
    result_json = main(answer_sheet_dir_path)
    print(json.dumps(result_json, ensure_ascii=False, indent=2))
