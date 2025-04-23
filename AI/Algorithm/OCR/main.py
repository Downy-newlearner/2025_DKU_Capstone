from ready_for_ocr.line_detection import detect_and_crop_by_lines
from ready_for_ocr.text_crop_final import process_images_in_directory
# from ready_for_ocr.using_OCR import recognizing
from easyocr.easyocr import *

def main():
    #10_answer.jpeg 이미지 처리
    detect_and_crop_by_lines(
        image_path='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/yolov10/test_splitted/10_answer.jpeg',
        output_dir='cropped_datasets/horizontally_cropped/answer',
        is_answer=True
    )
    
    # 10_question_number.jpeg 이미지 처리
    detect_and_crop_by_lines(
        image_path='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/yolov10/test_splitted/10_question_number.jpeg',
        output_dir='cropped_datasets/horizontally_cropped/question_number',
        is_answer=False
    )
    
    # text_crop의 process_images_in_directory 메서드 사용
    process_images_in_directory(
        input_dir='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/horizontally_cropped/answer',
        output_dir='cropped_datasets/text_crop/answer',
        is_answer=True
    )

    # text_crop의 process_images_in_directory 메서드 사용
    process_images_in_directory(
        input_dir='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/horizontally_cropped/question_number',
        output_dir='cropped_datasets/text_crop/question_number',
        is_answer=False
    )

    # recognizing(
    #     question_number_path='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/results_of_text_crop/question_number',
    #     answer_path='/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/cropped_datasets/results_of_text_crop/answer'
    # )

    # reader = Reader(['en'], gpu=True,
    #             model_storage_directory='model',
    #             user_network_directory='user_network',
    #             recog_network='custom')
    




if __name__ == "__main__":
    main()

