from pathlib import Path
from ultralytics import YOLO
from transformers import pipeline
import re

# --- Configuration ---
YOLO_MODEL_PATH = 'answer_recognition/preprocessing/yolov10_model/best.pt'
YOLO_CLASS_QN = 0
YOLO_CLASS_ANS = 1

# --- Global Model Loaders ---
yolo_model = None
try:
    if Path(YOLO_MODEL_PATH).exists():
        yolo_model = YOLO(YOLO_MODEL_PATH)
        print(f"YOLO model loaded successfully from {YOLO_MODEL_PATH}")
    else:
        print(f"YOLO model file not found at {YOLO_MODEL_PATH}")
except Exception as e:
    print(f"Error loading YOLO model: {e}")
    yolo_model = None

mnist_recognition_pipeline = None
try:
    mnist_recognition_pipeline = pipeline("image-classification", model="farleyknight/mnist-digit-classification-2022-09-04", device=-1) # cpu
    print("MNIST digit recognition model loaded successfully.")
except Exception as e:
    print(f"Error loading MNIST digit recognition model: {e}")
    mnist_recognition_pipeline = None

# --- Regex for Key Parsing ---
# 키 형식: "{과목명}_{학번}_{ansAreaID}_L{LineID}_x{xVAL}_qn{QN_STR_WITH_HYPHEN}_ac{ACVAL}(_dupN)?"
# 예: "Math_12345678_ansArea0_L0_x75_qn1-1_ac2"
# 예: "Science_87654321_ansArea1_L2_x100_qn10_ac1_dup1"
KEY_PARSING_REGEX = re.compile(
    r"^(?P<subject_student_id_base>.+?)"  # 1. 과목명_학번 (non-greedy)
    r"_(?P<ans_area_id>[a-zA-Z0-9]+)"     # 2. ansArea ID (e.g., ansArea0) - Not captured by name if not needed for grouping
    r"_L(?P<line_id>[a-zA-Z0-9]+)"        # 3. Line ID (e.g., L1) - Not captured by name
    r"_x(?P<x_val>\d+)"                   # 4. x_val (digits)
    r"_qn(?P<qn_str>[a-zA-Z0-9\-]+)"      # 5. qn_str (alphanumeric with hyphen)
    r"_ac(?P<ac_val>\d+)"                 # 6. ac_val (digits)
    r"(?:_dup\d+)?$"                      # 7. Optional _dupN suffix
) 