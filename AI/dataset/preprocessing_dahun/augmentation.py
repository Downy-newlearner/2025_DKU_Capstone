# 좌우 반전, 가우시안 노이즈, 좌우 반전 + 가우시안 노이즈 증강 -> 4배 증가

import os
import cv2
import numpy as np
from PIL import Image
import random

# 경로 설정
base_path = "/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/dataset/labels/train"

def augment_image(img, annotations, suffix):
    # 이미지 저장
    new_img_path = os.path.splitext(img_path)[0] + f"_{suffix}.jpg"
    cv2.imwrite(new_img_path, img)

    # 어노테이션 저장
    new_txt_path = os.path.splitext(txt_path)[0] + f"_{suffix}.txt"
    with open(new_txt_path, "w") as f:
        f.writelines(annotations)

def apply_augmentation(img_path, txt_path):
    # 이미지 로드
    img = cv2.imread(img_path)
    height, width = img.shape[:2]

    # 어노테이션 로드
    with open(txt_path, "r") as f:
        annotations = f.readlines()

    # 1. 좌우 반전
    flipped_img = cv2.flip(img, 1)
    flipped_annotations = []
    for line in annotations:
        parts = line.strip().split()
        class_id = parts[0]
        x_center, y_center, w, h = map(float, parts[1:])
        x_center = 1.0 - x_center  # 좌우 반전된 중심 좌표
        flipped_annotations.append(f"{class_id} {x_center} {y_center} {w} {h}\n")
    augment_image(flipped_img, flipped_annotations, "flipped")

    # 2. 가우시안 노이즈
    noise = np.random.normal(0, 25, img.shape).astype(np.uint8)
    noisy_img = cv2.add(img, noise)
    augment_image(noisy_img, annotations, "noisy")

    # 3. 좌우 반전 + 가우시안 노이즈
    noisy_flipped_img = cv2.add(flipped_img, noise)
    augment_image(noisy_flipped_img, flipped_annotations, "flipped_noisy")

# 파일 이름 중 가장 큰 숫자를 찾기
file_numbers = [int(os.path.splitext(f)[0]) for f in os.listdir(base_path) if f.endswith('.jpg')]
max_number = max(file_numbers)

print(f"{max_number}개의 파일을 {max_number * 4}개로 증강합니다.")

for i in range(1, max_number + 1):
    img_path = os.path.join(base_path, f"{i}.jpg")
    txt_path = os.path.join(base_path, f"{i}.txt")

    apply_augmentation(img_path, txt_path)

print("데이터 증강 완료!")