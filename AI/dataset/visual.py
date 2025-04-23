import cv2

# # resize 전
# # 이미지 파일 경로
image_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/train/1.jpg'

# # 어노테이션 파일 경로
# annotation_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/train/1.txt'

# # 이미지 불러오기
image = cv2.imread(image_path)
# height, width, _ = image.shape

# # resize 전 포인트
# x1 = int(0.1966 * width)
# y1 = int(0.5564 * height)
# cv2.circle(image, (x1, y1), 30, (0, 0, 255), -1)

# # 이미지 저장하기
# cv2.imwrite('/home/jdh251425/2025_DKU_Capstone/AI/dataset/center.jpg', image)





# resize 후
# 이미지 파일 경로
image_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/resized/1.jpg'

# 어노테이션 파일 경로
annotation_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/resized/1.txt'

# 이미지 불러오기
image_resized = cv2.imread(image_path)
height_resized, width_resized, _ = image.shape


# resize 후 포인트
x2 = int(0.101521 * width_resized)
y2 = int(0.203039 * height_resized)
cv2.circle(image_resized, (x2, y2), 30, (0, 0, 255), -1)


# 어노테이션 파일 읽기
with open(annotation_path, 'r') as file:
    lines = file.readlines()


    
# 각 어노테이션에 대해 사각형 그리기
for line in lines:
    parts = line.strip().split()
    class_id = int(parts[0])
    x_center = int(float(parts[1]) * width_resized)
    y_center = int(float(parts[2]) * height_resized)
    cv2.circle(image_resized, (x_center, y_center), 20, (255, 0, 255), -1)

# 이미지 저장하기
cv2.imwrite('/home/jdh251425/2025_DKU_Capstone/AI/dataset/center_resized.jpg', image_resized)
