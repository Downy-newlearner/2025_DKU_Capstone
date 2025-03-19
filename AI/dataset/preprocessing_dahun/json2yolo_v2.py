'''
Written by 정다훈 250318
CVAT에서 annotation을 json 형식으로 제공받는다.
YOLOv7 훈련을 위해서는 yolo 형식의 데이터셋이 필요하다.
yolo 데이터셋이란 훈련 데이터 폴더에 같은 이름을 가진 jpg(또는 다른 이미지 형식), txt(annotation) 쌍을 두는 형식이다.
본 코드는 json 파일(json_path)에 작성된 annotation 정보를 통해 label_dir에 annotation을 txt파일로 생성한다.
'''

import json
import os

json_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/annotations/instances_default_updated.json' # CVAT에서 제공받은 ann 파일(json 형식)
label_dir = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/train/' # 이 path는 '/'로 끝나게 설정해야함.

# 라벨 디렉토리가 존재하지 않으면 생성
os.makedirs(label_dir, exist_ok=True)

# JSON 파일 로드
with open(json_path) as f:
    dataset = json.load(f)

# 이미지 ID별로 어노테이션을 정리
annotations = {image['id']: [] for image in dataset['images']}

for ann in dataset['annotations']:
    annotations[ann['image_id']].append(ann)

# 라벨 파일 생성
for image in dataset['images']:
    image_id = image['id']
    width, height = image['width'], image['height']
    label_path = f'{label_dir}{image_id}.txt'

    with open(label_path, 'w') as f:
        for ann in annotations[image_id]:
            category_id = ann['category_id'] - 1  # 0부터 시작하도록 조정
            bbox = ann['bbox']
            x_center = (bbox[0] + bbox[2] / 2) / width
            y_center = (bbox[1] + bbox[3] / 2) / height
            bbox_width = bbox[2] / width
            bbox_height = bbox[3] / height

            f.write(f"{category_id} {x_center} {y_center} {bbox_width} {bbox_height}\n")