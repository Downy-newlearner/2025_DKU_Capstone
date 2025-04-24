import pandas as pd
import os


# 매칭 수행
def match(df, df_half):
    matches = []
    matched_indices = set()
    for i, row_half in df_half.iterrows():
        y_center_half = row_half['y_center']
        min_diff = float('inf')
        best_match = None
        best_index = None
        for j in range(max(0, i-10), min(len(df), i+10)):
            row = df.iloc[j]
            diff = abs(row['y_center'] - y_center_half)
            if diff < min_diff:
                min_diff = diff
                best_match = row
                best_index = j
        if best_match is not None:
            matches.append({
                'name': best_match['name'],
                'result_text': best_match['recognition_result'] if best_match['recognition_result'] else None,
                'result_half': row_half['recognition_result'] if row_half['recognition_result'] else None,
                'confident_text': round(best_match['confident'], 3),
                'confident_half': round(row_half['confident'], 3)
            })
            matched_indices.add(best_index)

    # 매칭되지 않은 df의 항목 추가
    for j, row in df.iterrows():
        if j not in matched_indices:
            matches.append({
                'name': row['name'],
                'result_text': row['recognition_result'] if row['recognition_result'] else None,
                'result_half': None,
                'confident_text': round(row['confident'], 3),
                'confident_half': 0.0
            })

    return pd.DataFrame(matches)


'''
<파라미터>
recognition_results, recognition_results_answer, half_cropped_recognition_results: 각각 질문 번호, 답변, 절반으로 잘린 이미지에 대한 OCR 결과를 포함하는 pandas.DataFrame 형식의 데이터프레임입니다.

<리턴값>
matching_qn, matching_ans: 질문 번호와 답변에 대한 매칭 결과를 포함하는 pandas.DataFrame 형식의 데이터프레임으로, 각각 matching_qn.csv와 matching_ans.csv로 저장됩니다.

<함수 내용>
데이터프레임을 변환하고 y_center를 계산한 후, 각 항목을 매칭하여 가장 유사한 항목을 찾고 그 결과를 CSV 파일로 저장합니다.
'''
def match_results(text_cropped_recognition_qn, text_cropped_recognition_ans, half_cropped_recognition_qn, half_cropped_recognition_ans):
    # DataFrame 변환
    df_qn = text_cropped_recognition_qn
    df_ans = text_cropped_recognition_ans
    df_half_qn = half_cropped_recognition_qn
    df_half_ans = half_cropped_recognition_ans

    # y_center 계산
    df_qn['y_center'] = (df_qn['y_top'] + df_qn['y_bottom']) / 2
    df_ans['y_center'] = (df_ans['y_top'] + df_ans['y_bottom']) / 2
    df_half_qn['y_center'] = (df_half_qn['y_top'] + df_half_qn['y_bottom']) / 2
    df_half_ans['y_center'] = (df_half_ans['y_top'] + df_half_ans['y_bottom']) / 2

    matching_qn = match(df_qn, df_half_qn)
    matching_ans = match(df_ans, df_half_ans)

    if __name__ == "__main__":
        if not os.path.exists('matching_result/match'):
            os.makedirs('matching_result/match')

        # CSV로 저장
        matching_qn.to_csv('matching_result/match/matching_qn.csv', index=False)
        matching_ans.to_csv('matching_result/match/matching_ans.csv', index=False)

    return matching_qn, matching_ans


'''
<파라미터>
- matching_qn: 질문 번호 매칭 결과를 담은 pandas.DataFrame. 컬럼: name, result_text, result_half, confident_text, confident_half.
- matching_ans: 답변 매칭 결과를 담은 pandas.DataFrame. 컬럼: name, result_text, result_half, confident_text, confident_half.

<리턴값>
- df_matching_result_qn: 질문 번호에 대한 최종 비교 결과를 담은 pandas.DataFrame. df_matching_result_qn.csv로 저장됨. 컬럼: name, result_text, result_half, confident_text, confident_half, matching_result.
- df_matching_result_ans: 답변에 대한 최종 비교 결과를 담은 pandas.DataFrame. df_matching_result_ans.csv로 저장됨. 컬럼: name, result_text, result_half, confident_text, confident_half, matching_result.

<함수 내용>
1. 내부 함수 compare 정의: 각 데이터프레임의 행을 순회하며 비교 수행.
2. 결과 결정: result_text 또는 result_half가 None 또는 'out'이면 matching_result를 'JSON'으로 설정, 그렇지 않으면 result_text 값으로 설정.
3. 결과 저장: 비교 결과를 df_matching_result_qn.csv와 df_matching_result_ans.csv로 저장.
'''
def compare_results(matching_qn, matching_ans):
    def compare(df):
        results = []
        for _, row in df.iterrows():
            if row['result_text'] in [None, 'out'] or row['result_half'] in [None, 'out']:
                matching_result = 'JSON'
            else:
                matching_result = row['result_text']
            results.append({
                'name': row['name'],
                'result_text': row['result_text'],
                'result_half': row['result_half'],
                'confident_text': row['confident_text'],
                'confident_half': row['confident_half'],
                'matching_result': matching_result
            })
        return pd.DataFrame(results)

    df_compare_result_qn = compare(matching_qn)
    df_compare_result_ans = compare(matching_ans)

    if __name__ == "__main__":  
        if not os.path.exists('matching_result/compare'):
            os.makedirs('matching_result/compare')

        # 결과를 CSV로 저장
        df_compare_result_qn.to_csv('matching_result/compare/compare_qn.csv', index=False)
        df_compare_result_ans.to_csv('matching_result/compare/compare_ans.csv', index=False)

    return df_compare_result_qn, df_compare_result_ans


# 비교 함수 호출
def process_and_compare_results(text_cropped_recognition_qn, text_cropped_recognition_ans, half_cropped_recognition_qn, half_cropped_recognition_ans):
    # 매칭 알고리즘을 사용하여 매칭 결과 생성
    df_matching_qn, df_matching_ans = match_results(
        text_cropped_recognition_qn, 
        text_cropped_recognition_ans, 
        half_cropped_recognition_qn, 
        half_cropped_recognition_ans
    )

    # 비교 함수로 최종 결과 생성
    df_compare_result_qn, df_compare_result_ans = compare_results(df_matching_qn, df_matching_ans)


    return df_matching_qn, df_matching_ans, df_compare_result_qn, df_compare_result_ans


if __name__ == "__main__":      
    df_recognition_results_question_number = pd.read_csv('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/use_ocr/recognition_results_qn.csv')
    df_recognition_results_answer = pd.read_csv('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/use_ocr/recognition_results_ans.csv')
    df_half_cropped_recognition_results = pd.read_csv('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/use_ocr/half_cropped_recognition_results.csv')

    # 함수 호출
    df_matching_result_qn, df_matching_result_ans = process_and_compare_results(df_recognition_results_question_number, df_recognition_results_answer, df_half_cropped_recognition_results)
