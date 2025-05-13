import subprocess

# YOLO 명령어
command = [
    "yolo",
    "task=detect",
    "mode=predict",
    "model=/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/preprocessing/yolov10_model/best.pt",
    "source=/home/jdh251425/2025_DKU_Capstone/AI/Algorithm/OCR/prac_data_0513/signals_and_systems_example.jpeg",
    "device=0"
]

# 명령어 실행
result = subprocess.run(command, capture_output=True, text=True)

# 결과 출력
print("stdout:", result.stdout)
print("stderr:", result.stderr)