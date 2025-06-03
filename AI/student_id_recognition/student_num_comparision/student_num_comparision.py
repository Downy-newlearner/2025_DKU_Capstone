'''
written by 정다훈 250521

- 함수 이름: student_num_comparision

- Param: `student_num` → int, `list` → list[int]
    - `student_num`: 학번
        - 8자리가 아니라면 바로 JSON으로
    - `list`
- Return: `go_to_JSON` → bool
    - 

- Logic:
    - if int(`student_num`) ≠ 8자리 정수
        - return True
    - (`student_num`을 `list`의 요소 하나하나와 각 자리를 비교하여 몇 자리가 겹치는지 확인)
    - 8자리 중 8자리가 겹치면 return False
    - 8자리 중 7자리 이하로 겹치면 return True

'''

def student_num_comparision(student_num: int, list: list[int]) -> bool:
    if student_num == None:
        return True

    # 학번이 8자리가 아닌 경우
    if len(str(student_num)) != 8:
        return True
    
    # 리스트의 각 학번과 비교
    for compare_num in list:
        # 비교할 학번도 8자리가 아닌 경우 건너뛰기
        if len(str(compare_num)) != 8:
            continue
            
        # 각 자리 비교
        matching_digits = 0
        student_str = str(student_num)
        compare_str = str(compare_num)
        
        for i in range(8):
            if student_str[i] == compare_str[i]:
                matching_digits += 1
        
        # 8자리 모두 일치하는 경우
        if matching_digits == 8:
            return False
    
    # 모든 비교가 끝났는데 8자리 일치하는 경우가 없었으면
    return True