'''
Written by 정다훈 0514

'''
import os

def preprocessing(dir):
    original_dir = os.path.join(dir, 'original_data')
    half_cropped_dir = os.path.join(dir, 'half_cropped')
    horizontally_cropped_dir = os.path.join(dir, 'horizontally_cropped')
    text_cropped_dir = os.path.join(dir, 'text_cropped')

    # Import modules
    from line_detection import detect_and_crop_by_lines
    from text_crop import process_images_in_directory

    # 원본 이미지(original_dir에 위치)를 입력으로 받아 half_cropped_dir에 저장하는 함수를 사용해야함 
        # YOLOv10 모델 사용에서 잠깐 막힘 0514 정다훈
        # 추후 코드 추가하길.
        # extract_bbox_from_txt.py 코드 추가하길.

    # line_detection.py에서 가로선 크롭
    detect_and_crop_by_lines(half_cropped_dir, horizontally_cropped_dir)

    # text_crop에서 텍스트 크롭
    process_images_in_directory(horizontally_cropped_dir)


if __name__ == '__main__':
    # Dataset path setting 
    dir ='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/prac_data_0513'
    preprocessing(dir)