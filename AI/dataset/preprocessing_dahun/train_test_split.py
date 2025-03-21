import os
import shutil
import random
from pathlib import Path


# 데이터 경로 설정
data_dir = Path("/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels/train")

# 저장할 폴더 경로 설정
base_save_dir = data_dir.parent
train_dir = base_save_dir / 'train'
val_dir = base_save_dir / 'val'
test_dir = base_save_dir / 'test'

# 폴더 생성
train_dir.mkdir(parents=True, exist_ok=True)
val_dir.mkdir(parents=True, exist_ok=True)
test_dir.mkdir(parents=True, exist_ok=True)

# 모든 파일 리스트 가져오기
all_files = list(data_dir.glob("*.jpg"))
random.shuffle(all_files)

# 파일 갯수 계산
total_files = len(all_files)
train_count = int(total_files * 0.7)
val_count = int(total_files * 0.15)

# split 데이터셋
train_files = all_files[:train_count]
val_files = all_files[train_count:train_count + val_count]
test_files = all_files[train_count + val_count:]

# 파일 이동 함수
def move_files(files, target_dir):
    for file in files:
        txt_file = file.with_suffix('.txt')
        if txt_file.exists():
            # 이미지 파일과 txt 파일 모두 이동
            shutil.move(str(file), target_dir / file.name)
            shutil.move(str(txt_file), target_dir / txt_file.name)

# 파일 이동
move_files(train_files, train_dir)
move_files(val_files, val_dir)
move_files(test_files, test_dir)

print("Data split complete!")