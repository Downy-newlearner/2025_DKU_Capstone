import pandas as pd
import os

def parsing_xlsx(xlsx_file_path: str) -> list:
    """
    XLSX 파일에서 '학번' 헤더를 찾아 그 아래 열의 데이터를 리스트로 추출합니다.
    최대 10열까지, 행 우선으로 '학번' 셀을 검색합니다.

    Args:
        xlsx_file_path (str): XLSX 파일 경로.

    Returns:
        list: 추출된 학번 리스트. '학번'을 찾지 못하거나 데이터가 없으면 빈 리스트 반환.
    """
    student_num_list = []
    header_found = False
    header_row_idx = -1
    header_col_idx = -1

    try:
        # 엑셀 파일을 읽되, 헤더를 명시적으로 지정하지 않아 모든 데이터를 가져옴
        # pandas는 기본적으로 첫 번째 행을 헤더로 인식하려고 하므로, header=None으로 설정
        df = pd.read_excel(xlsx_file_path, header=None)

        # 1행 1열부터 행 기준 순서대로 10열까지 '학번' 셀 찾기
        # DataFrame의 인덱스는 0부터 시작
        # 최대 검색 행은 DataFrame의 전체 행 수, 최대 검색 열은 10 또는 DataFrame의 전체 열 수 중 작은 값
        num_rows = df.shape[0]
        num_cols_to_search = min(10, df.shape[1])

        for r_idx in range(num_rows):
            for c_idx in range(num_cols_to_search):
                cell_value = df.iat[r_idx, c_idx]
                
                if isinstance(cell_value, str) and '학번' in cell_value:
                    header_found = True
                    header_row_idx = r_idx
                    header_col_idx = c_idx
                    break  # '학번' 찾으면 내부 루프 종료
            if header_found:
                break  # '학번' 찾으면 외부 루프 종료
        
        if header_found:
            # '학번' 셀 바로 아래 행부터 데이터 추출
            # header_row_idx + 1 부터 시작하여, NaN이 아닌 첫 데이터 셀을 찾는다.
            data_start_row_idx = -1
            for r_idx in range(header_row_idx + 1, num_rows):
                potential_data_cell = df.iat[r_idx, header_col_idx]
                if not pd.isna(potential_data_cell) and str(potential_data_cell).strip() != "":
                    data_start_row_idx = r_idx
                    break
            
            if data_start_row_idx != -1:
                # 실제 데이터가 시작되는 행부터 끝까지 또는 빈 셀을 만날 때까지 읽는다.
                for r_idx in range(data_start_row_idx, num_rows):
                    student_id_cell = df.iat[r_idx, header_col_idx]
                    if pd.isna(student_id_cell) or str(student_id_cell).strip() == "":
                        break  # 데이터가 없으면 중단
                    student_num_list.append(str(int(float(str(student_id_cell).strip())))) # 문자열로 변환 후 정수 변환, 다시 문자열로
            else:
                print(f"'{xlsx_file_path}' 파일에서 '학번' 헤더 아래 유효한 데이터를 찾을 수 없습니다.")
        else:
            print(f"'{xlsx_file_path}' 파일에서 '학번' 헤더를 찾을 수 없습니다.")

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {xlsx_file_path}")
    except Exception as e:
        print(f"XLSX 파일 처리 중 오류 발생 ({xlsx_file_path}): {e}")
    
    return student_num_list

if __name__ == '__main__':
    # 사용자가 제공한 경로로 테스트 코드를 작성합니다.
    xlsx_path = "/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/test_data/학적정보.xlsx"
    
    print(f"--- 테스트 시작: '{xlsx_path}' 파일 파싱 ---")
    student_numbers = parsing_xlsx(xlsx_path)
    
    if student_numbers:
        print(f"추출된 학번 리스트 (총 {len(student_numbers)}개):")
        for student_id in student_numbers:
            print(student_id)
    else:
        print("추출된 학번이 없습니다 또는 파일을 찾지 못했거나 오류가 발생했습니다.")
    print("--- 테스트 종료 ---")
   