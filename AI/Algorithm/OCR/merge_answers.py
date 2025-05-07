import pandas as pd
import numpy as np

# Load the CSV files
answers_df = pd.read_csv('/home/ysoh20/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/text_crop/answer.csv')
questions_df = pd.read_csv('/home/ysoh20/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/text_crop/question_number.csv')

def match(df_qn, df_ans): # answer.csv의 항목의 ytop ybottom으로 ycenter를 구함 -> qn 영역의 ytop, ybottom 사이에 있는지 확인하여 매칭
    matches = []
    matched_indices = set()
    
    # 각 질문 번호에 대해
    for i, row_qn in df_qn.iterrows():
        qn_y_top = row_qn['y_top']
        qn_y_bottom = row_qn['y_bottom']
        qn_y_center = (qn_y_top + qn_y_bottom) / 2
        
        # 답변의 y_center가 질문 번호의 y_top과 y_bottom 사이에 있는지 확인
        for j, row_ans in df_ans.iterrows():
            if j in matched_indices:
                continue
                
            ans_y_center = (row_ans['y_top'] + row_ans['y_bottom']) / 2
            
            # 답변의 y_center가 질문 번호의 범위 안에 있으면 매칭
            if qn_y_top <= ans_y_center <= qn_y_bottom:
                matches.append({
                    'question_number': row_qn['recognition_result'],
                    'answer': row_ans['recognition_result'],
                    'question_confidence': round(row_qn['confident'], 3),
                    'answer_confidence': round(row_ans['confident'], 3),
                    'question_y_range': f"{qn_y_top}-{qn_y_bottom}",
                    'question_y_center': qn_y_center,
                    'answer_y_range': f"{row_ans['y_top']}-{row_ans['y_bottom']}",
                    'answer_y_center': ans_y_center,
                    'is_matched': True
                })
                matched_indices.add(j)
                break
        
        # 매칭되는 답변이 없는 경우(예를 들어, qn 인식을 못한 경우)
        else:
            matches.append({
                'question_number': row_qn['recognition_result'],
                'answer': 'NO_MATCH',
                'question_confidence': round(row_qn['confident'], 3),
                'answer_confidence': 0.0,
                'question_y_range': f"{qn_y_top}-{qn_y_bottom}",
                'question_y_center': qn_y_center,
                'answer_y_range': 'N/A',
                'answer_y_center': 'N/A',
                'is_matched': False
            })

    # 매칭되지 않은 답변들 처리
    for j, row_ans in df_ans.iterrows():
        if j not in matched_indices:
            ans_y_center = (row_ans['y_top'] + row_ans['y_bottom']) / 2
            matches.append({
                'question_number': 'UNMATCHED_ANSWER',
                'answer': row_ans['recognition_result'],
                'question_confidence': 0.0,
                'answer_confidence': round(row_ans['confident'], 3),
                'question_y_range': 'N/A',
                'question_y_center': 'N/A',
                'answer_y_range': f"{row_ans['y_top']}-{row_ans['y_bottom']}",
                'answer_y_center': ans_y_center,
                'is_matched': False
            })

    result_df = pd.DataFrame(matches)
    # y_center를 기준으로 정렬
    result_df = result_df.sort_values(by=['answer_y_center'], 
                                    key=lambda x: pd.to_numeric(x, errors='coerce'))
    
    # 결과를 CSV로 저장
    result_df.to_csv('/home/ysoh20/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/text_crop/matched_results.csv', index=False)
    print("Matched results saved to ocr_results/text_crop/matched_results.csv")
    
    return result_df

# 매칭 실행
matched_results = match(questions_df, answers_df)