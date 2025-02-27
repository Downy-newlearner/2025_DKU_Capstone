import json

json_path = 'annotations2/instances_default.json'
output_path = 'annotations2/instances_default_updated.json'

# JSON 파일 로드
with open(json_path, 'r', encoding='utf-8') as f:
    dataset = json.load(f)

# 이미지 ID 매핑 생성
start_id = 23
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