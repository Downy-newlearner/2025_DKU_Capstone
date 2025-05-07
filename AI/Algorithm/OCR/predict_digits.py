from transformers import pipeline
import os
from PIL import Image
import cv2

# 모델 로드
pipe = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1)

# 이미지 폴더 경로
image_folder = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/experiments_0427/test'

# 이미지 파일 리스트 가져오기
def get_all_image_files(root_folder):
    image_files = []
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.jpeg') or filename.endswith('.jpg') or filename.endswith('.png'):
                image_files.append(os.path.join(dirpath, filename))
    return image_files

# 예측 수행
def predict_images(image_files):
    for image_file in image_files:
        image = Image.open(image_file)
        predictions = pipe(image)
        print(f"Predictions for {image_file}: {predictions}")

def recognize_images_from_bounding_boxes(text_crop_image_path, bounding_boxes):
    # 이미지 읽기
    image = cv2.imread(text_crop_image_path)

    recognition_results = []

    for (x, y, w, h) in bounding_boxes:
        # 바운딩 박스 영역 잘라내기
        cropped_image = image[y:y+h, x:x+w]
        cropped_pil_image = Image.fromarray(cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB))

        # 모델을 사용하여 예측
        predictions = pipe(cropped_pil_image)
        if predictions:
            # 가장 높은 확률의 예측 결과를 사용
            top_prediction = predictions[0]
            text, confidence = top_prediction['label'], top_prediction['score']
            if confidence > 0.85:
                recognition_results.append(((x + w//2, y + h//2), text))
            else:
                recognition_results.append(((x + w//2, y + h//2), 'JSON'))
        else:
            recognition_results.append(((x + w//2, y + h//2), 'JSON'))

    # x 좌표 기준으로 정렬
    recognition_results.sort(key=lambda x: x[0][0])

    return recognition_results

if __name__ == "__main__":
    image_files = get_all_image_files(image_folder)
    predict_images(image_files) 