import cv2
import supervision as sv
from ultralytics import YOLOv10  # YOLOv10 대신 YOLO 클래스를 사용

# 모델 로드 (GPU가 없으면 "cpu"로 변경)
model = YOLOv10("./weights/yolov10n.pt").to("cuda")  # GPU 사용

# 이미지 로드 (절대 경로 사용 추천)
image_path = "./bus.jpeg"
image = cv2.imread(image_path)

# OpenCV는 기본적으로 BGR이므로, RGB로 변환
image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

# 모델 추론 실행
results = model(image)[0]

# Supervision 라이브러리에서 Detections 객체 생성
detections = sv.Detections.from_ultralytics(results)

# Bounding Box 및 Label Annotator 설정
bounding_box_annotator = sv.BoundingBoxAnnotator()
label_annotator = sv.LabelAnnotator()

# 이미지에 바운딩 박스 및 라벨 추가
annotated_image = bounding_box_annotator.annotate(scene=image, detections=detections)
annotated_image = label_annotator.annotate(scene=annotated_image, detections=detections)

# OpenCV를 사용하여 이미지 저장 (RGB → BGR 변환 필요)
output_path = "./output_detected.jpg"
cv2.imwrite(output_path, cv2.cvtColor(annotated_image, cv2.COLOR_RGB2BGR))

print(f"✅ 결과 이미지가 저장되었습니다: {output_path}")