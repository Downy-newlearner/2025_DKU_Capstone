# 

import os
from PIL import Image

# 경로 설정
base_path = "/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/train"
save_path = "/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/resized"
target_size = (1280, 1280)

# 저장 경로가 없으면 생성
os.makedirs(save_path, exist_ok=True)

# 이미지 리사이즈 및 어노테이션 조정
for i in range(1, 166):
    img_path = os.path.join(base_path, f"{i}.jpg")
    txt_path = os.path.join(base_path, f"{i}.txt")
    save_img_path = os.path.join(save_path, f"{i}.jpg")
    save_txt_path = os.path.join(save_path, f"{i}.txt")

    try:
        # 이미지 리사이즈
        with Image.open(img_path) as img:
            original_size = img.size
            img = img.resize(target_size)
            img.save(save_img_path)

        # 어노테이션 조정
        with open(txt_path, "r") as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            class_id = parts[0]
            x_center, y_center, width, height = map(float, parts[1:])

            # 스케일 조정
            x_center *= target_size[0] / original_size[0]
            y_center *= target_size[1] / original_size[1]
            width *= target_size[0] / original_size[0]
            height *= target_size[1] / original_size[1]

            # 소수점 이하 자릿수 제한
            new_lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")

        with open(save_txt_path, "w") as f:
            f.writelines(new_lines)

    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {img_path} 또는 {txt_path}")
    except Exception as e:
        print(f"오류 발생: {e}")

print("완료!")