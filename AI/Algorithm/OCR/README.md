## cropped_datasets

전처리 과정에서 발생하는 데이터들이다.

1. half_cropped
   yolov10으로 따낸 바운더리를 기준으로 영역을 쪼갬

2. horizontally_cropped('line_detection'의 결과)
   half_cropped의 결과 이미지 2장(question_number, answer)에서 가로선을 기준으로 이미지를 조각냄

3. text_crop('text_crop_final'의 결과)
   horizontally_cropped의 조각 이미지에서 공백은 제거하고 텍스트만 1:1 비율로 잘라냄

## Packages

1. ready_for_ocr(데이터 크롭)

   - 답안지 이미지 전처리 패키지이다.

2. use_ocr

   - OCR을 수행하는 패키지이다.

3. match_and_make_JSON
   - OCR 결과를 question_number - answer 로 매칭하고 매칭 결과를 JSON으로 생성하는 패키지이다.
