import cv2

# 이미지 파일 경로
image_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/resized/1.jpg'

# 어노테이션 파일 경로
annotation_path = '/home/jdh251425/2025_DKU_Capstone/AI/dataset/labels_backup/resized/1.txt'

# 이미지 불러오기
image = cv2.imread(image_path)
height, width, _ = image.shape

# 어노테이션 파일 읽기
with open(annotation_path, 'r') as file:
    lines = file.readlines()

# 각 어노테이션에 대해 사각형 그리기
for line in lines:
    parts = line.strip().split()
    class_id = int(parts[0])
    x_center = float(parts[1]) * width
    y_center = float(parts[2]) * height
    box_width = float(parts[3]) * width
    box_height = float(parts[4]) * height

    # 좌상단 좌표 계산
    x1 = int(x_center - box_width / 2)
    y1 = int(y_center - box_height / 2)
    # 우하단 좌표 계산
    x2 = int(x_center + box_width / 2)
    y2 = int(y_center + box_height / 2)

    x3 = int(x_center)
    y3 = int(y_center)

    # 사각형 그리기
    cv2.circle(image, (x3, y3), 30, (0, 0, 255), -1)
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)

    print(f"height: {height}, width: {width}")
    print(f"x: {parts[1]}, y: {parts[2]}")

# 이미지 저장하기
cv2.imwrite('/home/jdh251425/2025_DKU_Capstone/AI/dataset/annotated_image_resized.jpg', image)
