import os
import json

# 경로를 지정해주자.
json_path = 'annotations2/instances_default_updated.json'
image_dir = "/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/dataset/캡스톤 23 인공지능 중간고사"


# JSON 파일 로드
with open('annotations2/instances_default_updated.json') as f:
    dataset = json.load(f)


# 각 이미지에 대해 ID에 기반하여 파일명 변경
for image_info in dataset['images']:
    current_name = image_info['file_name']
    new_name = f"{image_info['id']}.jpg"
    
    current_path = os.path.join(image_dir, current_name)
    new_path = os.path.join(image_dir, new_name)
    
    # 파일명 변경
    os.rename(current_path, new_path)

print("파일 이름 변경 완료.")