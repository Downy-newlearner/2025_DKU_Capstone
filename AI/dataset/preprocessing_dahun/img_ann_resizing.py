import os
from PIL import Image  # 이미지 처리를 위한 Pillow 라이브러리

# 경로 설정
base_path = "/Users/downy/Documents/2025_DKU_Capstone/2025_DKU_Capstone/AI/dataset/labels/train"
target_size = (1280, 1280)  # 목표 이미지 크기

# 이미지 리사이즈 및 어노테이션 조정
for i in range(1, 166):
    img_path = os.path.join(base_path, f"{i}.jpg")  # 이미지 파일 경로
    txt_path = os.path.join(base_path, f"{i}.txt")  # 어노테이션 파일 경로

    # 이미지 리사이즈
    with Image.open(img_path) as img:
        original_size = img.size  # 이미지의 원래 사이즈 저장
        img = img.resize(target_size)  # 이미지를 목표 크기로 리사이즈
        img.save(img_path)  # 리사이즈된 이미지를 저장
    
    # 어노테이션 조정
    with open(txt_path, "r") as f:
        lines = f.readlines()  # 어노테이션 파일의 모든 줄을 읽음
    
    new_lines = []
    for line in lines:
        parts = line.strip().split()  # 행을 공백 기준으로 분할
        class_id = parts[0]  # 클래스 ID
        x_center, y_center, width, height = map(float, parts[1:])  # 경계 상자 정보
        
        # 스케일 조정
        x_center *= target_size[0] / original_size[0]  # x 중심 좌표
        y_center *= target_size[1] / original_size[1]  # y 중심 좌표
        width *= target_size[0] / original_size[0]     # 경계 상자 너비
        height *= target_size[1] / original_size[1]    # 경계 상자 높이
        
        # 수정된 라인을 리스트에 추가
        new_lines.append(f"{class_id} {x_center} {y_center} {width} {height}\n")
    
    # 수정된 어노테이션을 파일에 저장
    with open(txt_path, "w") as f:
        f.writelines(new_lines)

print("완료!")  # 완료 메시지 출력