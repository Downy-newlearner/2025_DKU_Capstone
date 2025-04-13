import os
import cv2
from easyocr import Reader
import pandas as pd
import numpy as np




def perform_ocr(input_dir):
    # EasyOCR Reader 초기화
    reader = Reader(['en'], gpu=True,
                    model_storage_directory='model',
                    user_network_directory='user_network',
                    recog_network='custom')
    
    # Create result directory
    base_name = os.path.basename(input_dir)
    result_dir = os.path.join(os.path.dirname(input_dir), f'{base_name}_result')
    os.makedirs(result_dir, exist_ok=True)

    # Walk through the directory
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.endswith(('.png', '.jpg', '.jpeg')):
                file_path = os.path.join(root, file)
                image = cv2.imread(file_path)
                results = reader.readtext(image)

                # Create a white canvas with 3x padding
                h, w, _ = image.shape
                canvas = np.ones((h * 3, w * 3, 3), dtype=np.uint8) * 255

                # Calculate the position to place the original image
                start_x = w
                start_y = h

                # Place the original image in the center of the canvas
                canvas[start_y:start_y + h, start_x:start_x + w] = image

                # Perform rectangle and putText on the padded image
                for (bbox, text, confidence) in results:
                    (top_left, top_right, bottom_right, bottom_left) = bbox
                    top_left = (top_left[0] + start_x, top_left[1] + start_y)
                    bottom_right = (bottom_right[0] + start_x, bottom_right[1] + start_y)

                    # Draw rectangle
                    cv2.rectangle(canvas, top_left, bottom_right, (0, 255, 0), 2)

                    # Put text and confidence
                    cv2.putText(canvas, text, (top_left[0], top_left[1] - 5), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(canvas, f'{confidence:.2f}', (bottom_right[0], bottom_right[1]), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

                # Save the result image
                result_path = os.path.join(result_dir, file)
                cv2.imwrite(result_path, canvas)

# Example usage
perform_ocr('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/answer')
perform_ocr('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/text_crop/question_number')
