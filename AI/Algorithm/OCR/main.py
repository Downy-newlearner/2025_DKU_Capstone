'''
main.py
Written by 정다훈 2025.04.14

<이미지 전처리 과정>
1. 답안지 원본 이미지
2. half cropped 이미지
3. horizontally cropped 이미지
4. text crop 이미지 

전처리된 이미지는 모두 OCR/cropped_datasets/ 폴더에 저장됨


<OCR의 Input images>
1. half cropped 이미지 -> OCR 인식시켜 half_cropped_recognition_results.csv 생성
2. horizontally cropped 이미지 -> OCR 인식시켜 text_crop_recognition_results_question_number.csv 생성, text_crop_recognition_results_answer.csv 생성

'''


from preprocessing.line_detection import detect_and_crop_by_lines
from preprocessing.text_crop import process_images_in_directory

from recognition.OCR_to_half_cropped import perform_ocr_on_half_cropped
from recognition.OCR_to_text_crop import recognizing_images

from match_and_make_JSON.matching import process_and_compare_results
from match_and_make_JSON.JSON_to_grader import save_json_from_csv

from easyocr.easyocr import *
import pandas as pd
import os

def main():
    # 1. 답안지 원본 이미지 -> half cropped 이미지
    

    # 2. preprocessing.line_detection: half cropped 이미지 -> horizontally cropped 이미지
    half_cropped_dir = 'cropped_datasets/half_cropped'
    detect_and_crop_by_lines(
        image_path=os.path.join(half_cropped_dir, '10_answer.jpeg'),
        output_dir='cropped_datasets/horizontally_cropped/answer',
        is_answer=True
    )

    detect_and_crop_by_lines(
        image_path=os.path.join(half_cropped_dir, '10_question_number.jpeg'),
        output_dir='cropped_datasets/horizontally_cropped/question_number',
        is_answer=False
    )
    

    # 3. preprocessing.text_crop_final: horizontally cropped 이미지 -> text crop 이미지
    horizontally_cropped_dir = 'cropped_datasets/horizontally_cropped'
    process_images_in_directory(
        input_dir=os.path.join(horizontally_cropped_dir, 'answer'),
        output_dir='cropped_datasets/text_crop/answer',
        is_answer=True
    )

    process_images_in_directory(
        input_dir=os.path.join(horizontally_cropped_dir, 'question_number'),
        output_dir='cropped_datasets/text_crop/question_number',
        is_answer=False
    ) 


    # 4. use_ocr.OCR_to_half_images_debug: 
    # half cropped 이미지 -> OCR 인식시켜 half_cropped_recognition_results.csv 생성
    # 결과 csv 파일 저장 경로: ocr_results/half_cropped/
    half_cropped_dir = 'cropped_datasets/half_cropped' # 입력 이미지 경로
    os.makedirs('ocr_results/half_cropped', exist_ok=True) # 결과 csv 파일 저장 경로
    
    df_answer, df_question_number  = perform_ocr_on_half_cropped(input_dir=half_cropped_dir)

    df_answer.to_csv('ocr_results/half_cropped/answer.csv', index=False)
    df_question_number.to_csv('ocr_results/half_cropped/question_number.csv', index=False)


    # 5. use_ocr.OCR_to_text_crop: 
    # text crop 이미지 -> OCR 인식시켜 text_crop_recognition_results_question_number.csv 생성, text_crop_recognition_results_answer.csv 생성
    # 결과 csv 파일 저장 경로: ocr_results/text_crop/
    text_crop_dir = 'cropped_datasets/text_crop' # 입력 이미지 경로
    os.makedirs('ocr_results/text_crop', exist_ok=True) # 결과 csv 파일 저장 경로

    df_question_number = recognizing_images(
        image_path=os.path.join(text_crop_dir, 'question_number'),
        qn_or_ans='qn'
    )
    df_question_number.to_csv('ocr_results/text_crop/question_number.csv', index=False)

    df_answer = recognizing_images(
        image_path=os.path.join(text_crop_dir, 'answer'),
        qn_or_ans='ans'
    )
    df_answer.to_csv('ocr_results/text_crop/answer.csv', index=False)


    # 6. first_result.matching: 
    # 매칭 알고리즘을 사용하여 매칭 결과 생성
    # 결과 csv 파일 저장 경로: ocr_results/matching/

    df_text_cropped_recognition_qn = pd.read_csv('ocr_results/text_crop/question_number.csv')
    df_text_cropped_recognition_ans = pd.read_csv('ocr_results/text_crop/answer.csv')
    df_half_cropped_recognition_results_qn = pd.read_csv('ocr_results/half_cropped/question_number.csv')
    df_half_cropped_recognition_results_ans = pd.read_csv('ocr_results/half_cropped/answer.csv')

    # 함수 호출
    df_matching_qn, df_matching_ans, df_compare_result_qn, df_compare_result_ans = process_and_compare_results(df_text_cropped_recognition_qn, df_text_cropped_recognition_ans, df_half_cropped_recognition_results_qn, df_half_cropped_recognition_results_ans)

    os.makedirs('ocr_results/match', exist_ok=True) # 결과 csv 파일 저장 경로    
    os.makedirs('ocr_results/compare', exist_ok=True) # 결과 csv 파일 저장 경로

    df_matching_qn.to_csv('ocr_results/match/matching_qn.csv', index=False)
    df_matching_ans.to_csv('ocr_results/match/matching_ans.csv', index=False)
    df_compare_result_qn.to_csv('ocr_results/compare/compare_qn.csv', index=False)
    df_compare_result_ans.to_csv('ocr_results/compare/compare_ans.csv', index=False)


    # 7. match_and_make_JSON.JSON_to_grader: 
    # 매칭 결과 csv 파일을 JSON 파일로 변환
    # 결과 JSON 파일 저장 경로: ocr_results/JSON/
    os.makedirs('ocr_results/JSON', exist_ok=True) # 결과 JSON 파일 저장 경로

    save_json_from_csv(
        qn_csv_path='ocr_results/compare/compare_qn.csv',
        ans_csv_path='ocr_results/compare/compare_ans.csv',
        json_output_path='ocr_results/JSON/matching_results.json'
    )   


if __name__ == "__main__":
    main()

