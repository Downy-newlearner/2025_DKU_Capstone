from paddleocr import PaddleOCR
import cv2
import numpy as np

def detect_student_id(image_path):
    # Initialize PaddleOCR with English model
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    
    # Read the image
    img = cv2.imread(image_path)
    
    # Get OCR result
    result = ocr.ocr(img, cls=True)
    
    # Process results
    if result:
        for line in result:
            for word_info in line:
                text = word_info[1][0]  # Get detected text
                confidence = word_info[1][1]  # Get confidence score
                
                # Check if the text contains digits and has length similar to student ID
                if text.isdigit() and len(text) >= 6:  # Being a bit flexible with length
                    print(f"Detected Number: {text}")
                    print(f"Confidence: {confidence:.4f}")
                    
                    # Draw bounding box
                    points = word_info[0]
                    points = np.array(points).astype(np.int32)
                    cv2.polylines(img, [points], True, (0, 255, 0), 2)
                    
                    # Add text above the bounding box
                    cv2.putText(img, f"{text} ({confidence:.2f})", 
                              (points[0][0], points[0][1] - 10),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Save the annotated image
    output_path = 'result_paddle.jpg'
    cv2.imwrite(output_path, img)
    return output_path

if __name__ == "__main__":
    image_path = "number22.png"
    result_path = detect_student_id(image_path)
    print(f"Result saved to: {result_path}")