'''
Written by 정다훈 250318
CVAT에서 제공받은 annotation 정보가 담긴 json 파일에는 image의 파일명과 할당된 id가 존재한다.
yolo 형식의 데이터셋 구성을 위해 모든 파일명은 id로 대체되어야한다.
본 코드는 해당 작업을 수행한다.
'''

import os
import json

# 경로를 지정해주자.
json_path = r'/home/jdh251425/2025_DKU_Capstone/AI/dataset/annotations/instances_default_updated.json' # CVAT에서 제공받은 ann 파일(json 형식)
image_dir = r'/home/jdh251425/2025_DKU_Capstone/AI/dataset/Annotation'


# JSON 파일 로드
with open(json_path) as f:
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

