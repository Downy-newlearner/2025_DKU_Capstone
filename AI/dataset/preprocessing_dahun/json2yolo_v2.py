import json
import os

json_path = 'annotations2/instances_default_updated.json'
label_dir = 'labels/train/'

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