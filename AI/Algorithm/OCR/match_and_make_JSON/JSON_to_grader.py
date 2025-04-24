import pandas as pd
import os
import json

def save_json_from_csv(qn_csv_path, ans_csv_path, json_output_path):
    # CSV 파일 읽기
    df_qn = pd.read_csv(qn_csv_path)
    df_ans = pd.read_csv(ans_csv_path)

    # 'matching_result'가 'JSON'인 데이터 필터링
    df_qn_json = df_qn[df_qn['matching_result'] == 'JSON']
    df_ans_json = df_ans[df_ans['matching_result'] == 'JSON']

    # 이미지 주소 생성 함수
    def get_image_paths(name):
        base_path = f'/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/{name}'
        if os.path.exists(base_path):
            return [os.path.join(base_path, img) for img in os.listdir(base_path) if img.endswith(('.jpg', '.jpeg', '.png'))]
        return []

    # JSON 데이터 생성
    json_data = {}

    for _, row in df_qn_json.iterrows():
        name = row['name']
        json_data[name] = get_image_paths(name)

    for _, row in df_ans_json.iterrows():
        name = row['name']
        json_data[name] = get_image_paths(name)

    # JSON 파일로 저장
    with open(json_output_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

    print(f'JSON 파일이 {json_output_path}에 저장되었습니다.')

# 함수 호출 예시
# save_json_from_csv(qn_csv_path, ans_csv_path, json_output_path)

if __name__ == "__main__":
    # CSV 파일 경로
    qn_csv_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/compare/compare_qn.csv'
    ans_csv_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/compare/compare_ans.csv'

    # JSON 파일 경로
    json_output_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/ocr_results/JSON/matching_results.json'

    # 함수 호출
    save_json_from_csv(qn_csv_path, ans_csv_path, json_output_path)