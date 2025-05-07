import easyocr
import matplotlib.pyplot as plt
import cv2

# 이미지 파일 경로
image_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/original_data/10.jpg'

# EasyOCR Reader 객체 생성
reader = easyocr.Reader(['en'])  # 필요한 언어 코드 추가 가능

# 이미지에서 텍스트 추출
results = reader.readtext(image_path)

# 이미지 로드
image = cv2.imread(image_path)

# 결과 시각화
for (bbox, text, prob) in results:
    # 바운딩 박스 좌표 추출
    (top_left, top_right, bottom_right, bottom_left) = bbox
    top_left = tuple(map(int, top_left))
    bottom_right = tuple(map(int, bottom_right))

    # 바운딩 박스 그리기
    cv2.rectangle(image, top_left, bottom_right, (0, 255, 0), 2)

    # 텍스트와 확률 표시
    cv2.putText(image, f'{text} ({prob:.2f})', (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

# 이미지 저장 경로
output_image_path = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/original_data/10_processed.jpg'

# 이미지 저장
cv2.imwrite(output_image_path, image)
