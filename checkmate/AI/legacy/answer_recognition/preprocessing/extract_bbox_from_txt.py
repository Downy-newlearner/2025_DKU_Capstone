import os
from PIL import Image
import glob

# 경로 설정
IMAGE_DIR = "/home/elicer/DKU-Capstone-Yolov10/data/test/images2"  # 이미지가 있는 디렉토리 경로
LABEL_PATH = "results/exp12/labels/10_same_y_height.txt"  # 라벨 txt 파일 경로
OUTPUT_DIR = "cropped_images"  # 결과물 저장 디렉토리

def extract_and_save_bbox(image_path, bbox, class_id, output_path, output_filename):
    # Open the image
    img = Image.open(image_path)
    width, height = img.size-415
    
    # Convert normalized bbox coordinates to pixel coordinates
    x_center, y_center, bbox_width, bbox_height = bbox
    x1 = int((x_center - bbox_width/2) * width)
    y1 = int((y_center - bbox_height/2) * height)
    x2 = int((x_center + bbox_width/2) * width)
    y2 = int((y_center + bbox_height/2) * height)
    
    # Ensure coordinates are within image bounds
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(width, x2)
    y2 = min(height, y2)
    
    # Crop the image
    cropped_img = img.crop((x1, y1, x2, y2))
    
    # Create output directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    # Save the cropped image
    output_file_path = os.path.join(output_path, output_filename)
    cropped_img.save(output_file_path)
    print(f"Saved: {output_file_path}")

def main():
    # Get all image files in the image directory
    image_files = glob.glob(os.path.join(IMAGE_DIR, "*.jpg"))  # assuming jpg files
    
    # Read the label file
    with open(LABEL_PATH, 'r') as f:
        lines = f.readlines()
    
    # Process each image
    for image_path in image_files:
        image_name = os.path.splitext(os.path.basename(image_path))[0]
        
        if not os.path.exists(image_path):
            print(f"Warning: Image {image_path} not found. Skipping...")
            continue
        
        # Process each detection in the txt file
        for line in lines:
            if not line.strip():  # Skip empty lines
                continue
            
            # Parse the line
            parts = line.strip().split()
            if len(parts) != 5:  # Skip invalid lines
                continue
            
            class_id = int(parts[0])
            bbox = [float(x) for x in parts[1:]]  # x_center, y_center, width, height
            
            # Define output filename based on class_id
            if class_id == 0:
                output_filename = f"{image_name}_question_number.jpg"
            else:
                output_filename = f"{image_name}_answer.jpg"
            
            # Extract and save the bbox
            extract_and_save_bbox(image_path, bbox, class_id, OUTPUT_DIR, output_filename)

    print("Extraction completed!")

if __name__ == "__main__":
    main() 