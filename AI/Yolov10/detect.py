from ultralytics import YOLOv10

model = YOLOv10(f'./weights/yolov10m.pt')
results = model(source=f'./bus.jpeg', conf=0.25)
print(results[0].boxes.xyxy)
print(results[0].boxes.conf)
print(results[0].boxes.cls)