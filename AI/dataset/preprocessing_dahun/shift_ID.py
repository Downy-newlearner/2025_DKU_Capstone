'''
Written by 정다훈 250318
CVAT에서 task를 여러 개로 두어서 어노테이션 작업을 한 경우 json파일이 task 개수만큼 여러개 발생하는 경우가 존재한다.
이런 경우 각 json파일의 image_id는 1부터 시작하므로 이를 조정해야한다.
1번째 json파일의 image_id가 22까지 존재한다면 2번째 json파일의 image_id는 23부터 시작해야할 것이다.
본 코드는 이 작업을 수행한다.
'''
import json

json_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/annotations/instances_default.json'
output_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/annotations/instances_default_updated.json'

# JSON 파일 로드
with open(json_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# 이미지 ID 매핑 생성
start_id = 166
id_mapping = {}
for i, image_info in enumerate(dataset['images'], start=start_id):
    old_id = image_info['id']
    image_info['id'] = i
    id_mapping[old_id] = i  # 이전 ID에서 새로운 ID로 매핑

# 어노테이션의 image_id 업데이트
for annotation in dataset['annotations']:
    old_image_id = annotation['image_id']
    if old_image_id in id_mapping:
        annotation['image_id'] = id_mapping[old_image_id]

# 변경된 JSON 파일 저장
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(dataset, f, ensure_ascii=False, indent=4)

print("ID 업데이트 완료.")