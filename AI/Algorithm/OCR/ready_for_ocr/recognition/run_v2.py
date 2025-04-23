from easyocr.easyocr import *
import os
from PIL import Image, ImageDraw

# GPU 설정
os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'

def get_files(path):
    file_list = []
    files = [f for f in os.listdir(path) if not f.startswith('.')]  # skip hidden file
    files.sort()
    abspath = os.path.abspath(path)
    for file in files:
        file_path = os.path.join(abspath, file)
        file_list.append(file_path)
    return file_list, len(file_list)

if __name__ == '__main__':
    # Using custom model
    reader = Reader(['en'], gpu=True,
                    model_storage_directory='model',
                    user_network_directory='user_network',
                    recog_network='custom')

    files, count = get_files('/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/yolov10/test_splitted')

    # 결과 저장 디렉토리
    output_dir = './output/after_split_by_yooseok_0408'
    os.makedirs(output_dir, exist_ok=True)

    for idx, file in enumerate(files):
        filename = os.path.basename(file)
        result = reader.readtext(file)

        # 원본 이미지 열기
        img = Image.open(file)
        draw = ImageDraw.Draw(img)

        # 바운딩 박스 그리기
        for (bbox, string, confidence) in result:
            draw.polygon([tuple(point) for point in bbox], outline='red')
            print("filename: '%s', confidence: %.4f, string: '%s'" % (filename, confidence, string))
            # print('bbox: ', bbox)

        # 결과 이미지 저장
        output_path = os.path.join(output_dir, filename)
        img.save(output_path)
        print(f"Processed image saved to {output_path}")