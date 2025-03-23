import os
from PIL import Image

def resize_images_in_folder(input_folder: str, output_folder: str, size: tuple = (640, 640)):
    """
    폴더 내의 모든 이미지를 지정된 크기로 변경하고 저장합니다.
    
    :param input_folder: 원본 이미지가 있는 폴더 경로
    :param output_folder: 변경된 이미지를 저장할 폴더 경로
    :param size: 변경할 크기 (기본값: 640x640)
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    for filename in os.listdir(input_folder):
        input_path = os.path.join(input_folder, filename)
        output_path = os.path.join(output_folder, filename)
        
        if os.path.isdir(input_path):
            print(f"{input_path}는 디렉토리입니다. 건너뜁니다.")
            continue
        
        try:
            with Image.open(input_path) as img:
                resized_img = img.resize(size, Image.LANCZOS)
                resized_img.save(output_path)
                print(f"{filename} -> {output_path} (크기 변경 완료)")
        except Exception as e:
            print(f"{filename} 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    input_folder = "/home/elicer/yolov10/image_resize"  # 원본 이미지 폴더 경로
    output_folder = "/home/elicer/yolov10/image_resize/resizing"  # 변경된 이미지 저장 폴더 경로
    resize_images_in_folder(input_folder, output_folder)
