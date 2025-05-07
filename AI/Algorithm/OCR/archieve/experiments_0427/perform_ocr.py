import os
import cv2
from easyocr import Reader


def perform_ocr_on_test_images(input_dir, output_dir):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=False)

    # 결과를 저장할 리스트
    results = []

    # input_dir를 os walk로 순회
    image_paths = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(('.jpeg', '.jpg', '.png')):
                image_paths.append(os.path.join(root, file))

    # 결과 이미지를 저장할 디렉토리 생성
    os.makedirs(output_dir, exist_ok=True)

    # 각 이미지 파일에 대해 OCR 수행
    for image_path in image_paths:
        # 이미지 읽기
        img = cv2.imread(image_path)
        if img is not None:
            # EasyOCR로 OCR 수행
            ocr_results = reader.readtext(img, detail=1, paragraph=False)

            # 각 인식 결과에 대해 처리
            for result in ocr_results:
                bbox, text, confidence = result
                (top_left, top_right, bottom_right, bottom_left) = bbox
                top_left = tuple(map(int, top_left))
                bottom_right = tuple(map(int, bottom_right))

                # 바운딩 박스 그리기
                cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 2)

                # 텍스트 그리기
                cv2.putText(img, text, (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # 결과 리스트에 추가
                results.append({
                    'image_path': image_path,
                    'y_top': top_left[1],
                    'y_bottom': bottom_right[1],
                    'confident': round(confidence, 3),
                    'recognition_result': text
                })

            # 결과 이미지 저장
            result_image_path = os.path.join(output_dir, os.path.basename(image_path))
            cv2.imwrite(result_image_path, img)

    # 결과를 텍스트 파일로 저장
    results_txt_path = os.path.join(output_dir, 'ocr_results.txt')
    with open(results_txt_path, 'w') as f:
        for result in results:
            f.write(f"Image: {result['image_path']}, Top: {result['y_top']}, Bottom: {result['y_bottom']}, Confidence: {result['confident']}, Text: {result['recognition_result']}\n")

    return results


if __name__ == "__main__":
    input_directory = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/test'
    output_directory = '/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/experiments_0427'
    results = perform_ocr_on_test_images(input_directory, output_directory)

    # 결과를 텍스트 파일로 저장
    results_txt_path = os.path.join(output_directory, 'ocr_results.txt')
    with open(results_txt_path, 'w') as f:
        for result in results:
            f.write(f"Image: {result['image_path']}, Top: {result['y_top']}, Bottom: {result['y_bottom']}, Confidence: {result['confident']}, Text: {result['recognition_result']}\n") 