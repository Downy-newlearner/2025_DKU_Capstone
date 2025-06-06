import sys # 경로 추가를 위해 import
from flask import Flask, request, jsonify, current_app, send_file # send_file 추가
import os
import tempfile
import traceback
import zipfile # decompression 모듈 내부에서 사용하지만, 여기서도 파일 타입 체크 등에 사용 가능
import pandas as pd # XLSX 처리용
from werkzeug.utils import secure_filename # 주석 해제 또는 다시 추가
import uuid # UUID 추가
import shutil # 백그라운드 작업에서 임시 폴더 삭제용
import json # KafkaProducer value_serializer에서 사용되므로 필요, Flask jsonify와는 다름
import unicodedata # 유니코드 정규화 위해 추가
# import re # 이제 사용 안 함

import threading
from kafka import KafkaProducer
# Flask의 jsonify와 이름 충돌을 피하기 위해 json 모듈은 보통 그대로 사용합니다.
# value_serializer에서 json.dumps를 사용하므로 import json은 필요합니다.

# PDF 및 그래프 생성용 라이브러리 임포트
import io
import matplotlib
matplotlib.use('Agg') # 백엔드에서 Matplotlib 사용을 위한 설정
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


# TODO: 각 모듈의 main 함수 또는 필요한 함수들을 import
# from AI.Student_id_recognition.main import main as process_student_ids # 예시
# from AI.Algorithm.OCR.main_recognition import main_recognition_process # 예시

# 애플리케이션 루트 경로를 기준으로 모듈 경로 추가
# 이 방법은 모든 환경에서 권장되지는 않으며, Python 패키지 구조를 사용하는 것이 더 좋습니다.
APP_ROOT = os.path.dirname(os.path.abspath(__file__))
AI_MODULE_PATH = os.path.join(APP_ROOT, 'AI') # AI 폴더 경로
if AI_MODULE_PATH not in sys.path:
    sys.path.insert(0, AI_MODULE_PATH)

# Student_id_recognition 모듈 import
from student_id_recognition.main import main as process_student_ids
from student_id_recognition.main import make_json as make_student_id_json # make_json도 가져오기
from student_id_recognition.decompression_parsing.decompression import extract_archive
from student_id_recognition.decompression_parsing.parsing_xlsx import parsing_xlsx # parsing_xlsx 임포트 추가

# Algorithm.OCR 모듈 import (recognize_answer_endpoint에서 사용되었었음)
# from answer_recognition.main import main_recognition_process 
# from answer_recognition.main import DEFAULT_QN_DIRECTORY_PATH, DEFAULT_ANSWER_JSON_PATH, DEFAULT_OCR_RESULTS_JSON_PATH

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False # 한글을 ASCII로 이스케이프하지 않도록 설정

# Kafka 프로듀서 설정 (Flask 초기화 시에 생성해두는 것을 권장)
# bootstrap_servers는 실제 환경에 맞게 수정해야 합니다.
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers='43.202.183.74:9092', # TODO: 실제 Kafka 서버 주소로 변경!
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    app.logger.info("Kafka Producer initialized successfully.")
except Exception as e:
    app.logger.error(f"Failed to initialize Kafka Producer: {e}. Background tasks might not send Kafka messages.")
    # Kafka 연결 실패 시 프로듀서가 None으로 유지됩니다.
    # 백그라운드 작업에서 producer 사용 전 None 체크 필요.

# 위 방식 대신, 앱 초기화 시점에 생성
UPLOAD_FOLDER_BASE = os.path.join(tempfile.gettempdir(), 'ocr_flask_uploads')
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
app.config['UPLOAD_FOLDER_BASE'] = UPLOAD_FOLDER_BASE

# 영구 파일 저장을 위한 기본 폴더 설정 -> APP_ROOT를 직접 사용하도록 변경
# PERMANENT_UPLOAD_FOLDER = os.path.join(APP_ROOT, 'permanent_uploads') # 앱 루트 하위에 'permanent_uploads' 폴더로 지정
# os.makedirs(PERMANENT_UPLOAD_FOLDER, exist_ok=True)
# app.config['PERMANENT_UPLOAD_FOLDER'] = PERMANENT_UPLOAD_FOLDER

# 필요한 경우 로깅 설정
import logging
logging.basicConfig(level=logging.INFO) # INFO 레벨로 변경

ALLOWED_EXTENSIONS_ZIP = {'zip'}
ALLOWED_EXTENSIONS_XLSX = {'xlsx'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/health', methods=['GET'])
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({"status": "healthy", "message": "OCR service is running."}), 200

def background_task(subject_name, zip_path, xlsx_path, extracted_images_path, processing_folder_path, parent_logger):
    logger = parent_logger # 전달받은 로거 사용
    try:
        logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 작업 시작.")
        # 4. 압축 해제
        if not extract_archive(zip_path, extracted_images_path):
            logger.error(f"[BG TASK - {os.path.basename(processing_folder_path)}] 압축 해제 실패: {zip_path}")
            return
        logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 압축 해제 완료: {zip_path} -> {extracted_images_path}")

        # 5. XLSX 파싱
        student_numbers_from_xlsx = []
        if os.path.exists(xlsx_path):
            try:
                student_numbers_from_xlsx = parsing_xlsx(xlsx_file_path=xlsx_path)
                logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] XLSX 파싱 완료. 학번 {len(student_numbers_from_xlsx)}개 로드.")
            except Exception as e:
                logger.error(f"[BG TASK - {os.path.basename(processing_folder_path)}] XLSX 파싱 오류 ({xlsx_path}): {e}")
        else:
            logger.warning(f"[BG TASK - {os.path.basename(processing_folder_path)}] XLSX 파일 없음: {xlsx_path}")

        # 6. 학번 인식 (및 조건부 파일명 변경)
        logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 학번 인식 모듈 호출 (subject_name: {subject_name})...")
        
        # Define Kafka topic for student_id_recognition module
        student_id_recognition_topic = "student-id-recognition-progress" # Or any other appropriate topic name
        task_identifier = os.path.basename(processing_folder_path)

        # process_student_ids (main.main) 함수에 subject_name 인자 전달
        result_from_module = process_student_ids(
            extracted_images_path,
            student_numbers_from_xlsx,
            subject_name,
            producer, # Pass the Kafka producer
            student_id_recognition_topic, # Pass the Kafka topic
            task_identifier # Pass a task_id
        )
        
        # main.py의 main 함수가 반환하는 result_json은 이미 subject 필드를 포함하고 있으므로,
        # 여기서 다시 설정할 필요가 없습니다. (또는 main.py에서 설정된 값을 신뢰)
        # result_from_module["subject"] = subject_name # 이 줄은 필요 없거나, main.py의 반환값을 확인 후 결정
        
        # 1차 인식 결과에 session_id 추가 (추후 상태 추적 또는 결과 매칭에 사용 가능)
        result_from_module["processing_folder"] = os.path.basename(processing_folder_path)
        logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 학번 인식 완료. Kafka 전송 대상 이미지 수: {len(result_from_module.get('lowConfidenceImages', []))}")

        # 7. Kafka로 결과 전송 (2차 수정이 필요한 이미지 정보만 전송됨)
        if producer:
            try:
                topic_name = "student-id-image-requests" # 필요시 토픽명 변경
                producer.send(topic_name, result_from_module)
                producer.flush()
                logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] Kafka 전송 완료. Topic: {topic_name}, Message: {result_from_module}")
            except Exception as e:
                logger.error(f"[BG TASK - {os.path.basename(processing_folder_path)}] Kafka 메시지 전송 실패: {e}")
        else:
            logger.error(f"[BG TASK - {os.path.basename(processing_folder_path)}] Kafka Producer not available. Skipping message send.")

    except Exception as e:
        logger.error(f"[BG TASK - {os.path.basename(processing_folder_path)}] 백그라운드 작업 중 예외 발생: {traceback.format_exc()}")
    finally:
        if os.path.exists(processing_folder_path):
            logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 백그라운드 작업 완료. 처리 폴더 ({processing_folder_path})는 유지됩니다.")
        else:
            logger.info(f"[BG TASK - {os.path.basename(processing_folder_path)}] 백그라운드 작업 완료. 처리 폴더가 존재하지 않습니다.")

@app.route('/recognize/student_id', methods=['POST'])
def recognize_student_id_endpoint():
    session_temp_dir = None # finally 또는 except에서 사용하기 위해 try 바깥에 선언
    try:
        subject_name = request.form.get('subject')
        app.logger.info(f"[recognize_student_id] Received subject_name from form: '{subject_name}'") # 로그 추가
        zip_file_obj = request.files.get('answerSheetZip')
        xlsx_file_obj = request.files.get('attendanceSheet')

        app.logger.debug(f"Request form: {request.form}, files: {request.files}")

        if not subject_name:
            return jsonify({"error": "Missing 'subject' in form data"}), 400
        if not zip_file_obj:
            return jsonify({"error": "Missing 'answerSheetZip' in files"}), 400
        if not xlsx_file_obj:
            return jsonify({"error": "Missing 'attendanceSheet' in files"}), 400

        if zip_file_obj.filename == '' or xlsx_file_obj.filename == '':
            return jsonify({"error": "File name cannot be empty"}), 400
        
        if not allowed_file(zip_file_obj.filename, ALLOWED_EXTENSIONS_ZIP):
            return jsonify({"error": "Invalid zip_file type"}), 400
        if not allowed_file(xlsx_file_obj.filename, ALLOWED_EXTENSIONS_XLSX):
            return jsonify({"error": "Invalid xlsx_file type"}), 400

        # session_temp_dir = tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER_BASE']) # 기존 임시폴더 생성 코드 주석 처리
        # app.logger.info(f"세션 임시 폴더 생성: {session_temp_dir} (ID: {os.path.basename(session_temp_dir)})")

        # 과목명으로 폴더 경로 설정 및 생성 (원본 subject_name 사용)
        subject_name_for_path = subject_name if subject_name else uuid.uuid4().hex # subject_name이 비어있을 경우 대비
        app.logger.info(f"[recognize_student_id] subject_name_for_path: '{subject_name_for_path}'")
        subject_data_path = os.path.join(APP_ROOT, subject_name_for_path)
        os.makedirs(subject_data_path, exist_ok=True)
        app.logger.info(f"과목 데이터 폴더 생성/확인: {subject_data_path}")

        original_zip_filename = zip_file_obj.filename
        original_xlsx_filename = xlsx_file_obj.filename
        zip_name_part, zip_ext_part = os.path.splitext(original_zip_filename)
        xlsx_name_part, xlsx_ext_part = os.path.splitext(original_xlsx_filename)
        
        # 파일명 부분 (원본 이름 또는 UUID 사용)
        zip_name_part_for_filename = zip_name_part if zip_name_part else uuid.uuid4().hex
        xlsx_name_part_for_filename = xlsx_name_part if xlsx_name_part else uuid.uuid4().hex

        zip_filename = zip_name_part_for_filename + zip_ext_part
        xlsx_filename = xlsx_name_part_for_filename + xlsx_ext_part

        zip_path = os.path.join(subject_data_path, zip_filename)
        xlsx_path = os.path.join(subject_data_path, xlsx_filename)
        
        zip_file_obj.save(zip_path)
        xlsx_file_obj.save(xlsx_path)
        app.logger.info(f"파일 저장 완료: {zip_path}, {xlsx_path}")

        # 원본 ZIP 파일명 기반으로 압축 해제 폴더명 생성 (원본 이름 또는 UUID 사용)
        original_zip_name_for_folder, _ = os.path.splitext(original_zip_filename)
        zip_folder_name_for_extraction = original_zip_name_for_folder if original_zip_name_for_folder else uuid.uuid4().hex
        app.logger.info(f"[recognize_student_id] original_zip_name_for_folder '{original_zip_name_for_folder}' -> zip_folder_name_for_extraction '{zip_folder_name_for_extraction}'")
        
        extracted_images_path = os.path.join(subject_data_path, zip_folder_name_for_extraction)
        os.makedirs(extracted_images_path, exist_ok=True)
        app.logger.info(f"압축 해제 대상 폴더 생성/확인: {extracted_images_path}")

        thread = threading.Thread(
            target=background_task,
            args=(subject_name, zip_path, xlsx_path, extracted_images_path, subject_data_path, app.logger),
            name=f"BGTask-{subject_name_for_path}-{zip_folder_name_for_extraction}"
        )
        thread.start()
        app.logger.info(f"백그라운드 스레드 시작됨 ({thread.name}) for subject folder: {subject_data_path}")

        return jsonify({"status": "processing_started", 
                        "message": "Files received and student ID recognition process started in background.",
                        "subject_folder": subject_data_path, 
                        "zip_folder_name": zip_folder_name_for_extraction
                        }), 202

    except Exception as e:
        app.logger.error(f"recognize_student_id_endpoint 예외 발생: {traceback.format_exc()}")
        # subject_data_path 변수가 이 블록에서 사용될 수 있도록, try 시작 전에 None으로 초기화 필요
        # 이 수정에서는 일단 해당 변수가 항상 할당된다고 가정하고, 삭제 로직만 제거합니다.
        # if subject_data_path and os.path.exists(subject_data_path): # 메인 스레드 오류 시 폴더 정리 로직 제거
        #     try:
        #         shutil.rmtree(subject_data_path)
        #         app.logger.info(f"오류 발생으로 과목 폴더 ({subject_data_path}) 삭제.")
        #     except Exception as e_rm:
        #         app.logger.warning(f"오류 발생 후 과목 폴더 ({subject_data_path}) 삭제 실패: {e_rm}")
        app.logger.info(f"오류 발생. 생성된 과목 폴더 ({subject_data_path if 'subject_data_path' in locals() else 'N/A'})는 유지됩니다.")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# --- 2차 답안 인식 엔드포인트 (Kafka 기반 아키텍처와 호환성 재검토 필요) ---
@app.route('/recognize/answer', methods=['POST'])
def recognize_answer_endpoint():
    """2차 답안 인식 엔드포인트: Spring으로부터 수정된 학번 정보를 받아 파일명 변경을 백그라운드로 시작합니다.
       대상 과목 폴더 내에 단 하나의 압축 해제된 ZIP 폴더가 있다고 가정합니다.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        subject_name = data.get('subject')
        app.logger.info(f"[recognize_answer] Received subject_name from JSON: '{subject_name}'")
        student_list = data.get('student_list')

        if not subject_name:
            return jsonify({"error": "Missing required field: subject"}), 400
        if not student_list:
            return jsonify({"error": "Missing required field: student_list"}), 400

        if not isinstance(subject_name, str) or not isinstance(student_list, list):
            return jsonify({"error": "Invalid data type for subject or student_list."}), 400

        subject_name_for_path = subject_name if subject_name else uuid.uuid4().hex # 원본 subject_name 또는 UUID 사용
        app.logger.info(f"[recognize_answer] subject_name_for_path: '{subject_name_for_path}'")
        subject_path = os.path.join(APP_ROOT, subject_name_for_path)

        if not os.path.isdir(subject_path):
            app.logger.error(f"Subject path not found: {subject_path}")
            return jsonify({"error": f"Directory for subject '{subject_name_for_path}' not found."}), 404

        # 과목 폴더 내의 하위 디렉토리(ZIP 폴더) 찾기
        try:
            subdirectories = [d for d in os.listdir(subject_path) if os.path.isdir(os.path.join(subject_path, d))]
        except OSError as e:
            app.logger.error(f"Error listing subdirectories in {subject_path}: {e}")
            return jsonify({"error": f"Could not read subject directory contents for '{subject_name_for_path}'."}), 500

        if len(subdirectories) == 0:
            app.logger.error(f"No subdirectories (zip folders) found in {subject_path} for subject '{subject_name_for_path}'.")
            return jsonify({"error": f"No processed zip folder found for subject '{subject_name_for_path}'. Please upload files first via /recognize/student_id."}), 404
        elif len(subdirectories) > 1:
            app.logger.error(f"Multiple subdirectories found in {subject_path} for subject '{subject_name_for_path}': {subdirectories}. Cannot determine target.")
            return jsonify({"error": f"Multiple processed zip folders found for subject '{subject_name_for_path}'. Please ensure only one target exists or specify the target."}), 409 # 409 Conflict
        
        target_zip_folder_name = subdirectories[0] # 유일한 하위 디렉토리 (recognize_student_id에서 원본 기준으로 생성된 이름)
        app.logger.info(f"Found single target zip folder: '{target_zip_folder_name}' in {subject_path}")

        base_image_path = os.path.join(subject_path, target_zip_folder_name)
        app.logger.info(f"Target base image path for rename: {base_image_path}")

        if not os.path.isdir(base_image_path):
            app.logger.error(f"Determined base image path is not a directory: {base_image_path}")
            return jsonify({"error": f"Internal error: Target path '{target_zip_folder_name}' for subject '{subject_name_for_path}' is not a valid directory."}), 500

        # 백그라운드 스레드 생성 및 시작
        thread = threading.Thread(
            target=background_rename_files_task,
            args=(
                subject_name, # background_rename_files_task는 원본 subject_name을 아직 사용할 수 있음 (로깅 등)
                student_list, 
                base_image_path, 
                app.logger, 
            ),
            name=f"BGRenameTask-{subject_name_for_path}-{target_zip_folder_name}"
        )
        thread.start()

        task_info_id = f"{subject_name_for_path}-{target_zip_folder_name}"
        app.logger.info(f"백그라운드 파일명 변경 스레드 시작됨 ({thread.name}) for {task_info_id}")

        return jsonify({
            "status": "processing_started",
            "message": "File renaming process started in background.",
            "task_reference_id": task_info_id 
        }), 202

    except Exception as e:
        app.logger.error(f"Error in /recognize/answer endpoint (before starting background task): {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

def background_rename_files_task(subject_name, student_list, base_image_path, parent_logger):
    logger = parent_logger
    task_id = f"rename-{secure_filename(subject_name)}-{uuid.uuid4().hex[:8]}"
    logger.info(f"[BG RENAME TASK - {task_id}] 작업 시작. Target path: {base_image_path}")

    results = []
    renamed_count = 0
    error_count = 0
    skipped_count = 0
    known_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

    try:
        logger.info(f"[BG RENAME TASK - {task_id}] Attempting to list files in: {base_image_path}")
        # normalized_to_raw_map: NFC 정규화된 파일명을 key로, 원본(raw) 파일명을 value로 저장
        normalized_to_raw_map = {}
        try:
            for f_raw in os.listdir(base_image_path):
                if os.path.isfile(os.path.join(base_image_path, f_raw)):
                    f_normalized_nfc = unicodedata.normalize('NFC', f_raw)
                    if f_normalized_nfc in normalized_to_raw_map:
                        # 만약 NFC 정규화 후 이름이 충돌하면 로그 남기고 둘 다 처리하지 않거나,
                        # 혹은 리스트로 관리하여 더 복잡한 로직을 수행해야 할 수 있음.
                        # 여기서는 일단 마지막에 발견된 raw 파일명으로 덮어쓰지만, 가능성은 낮음.
                        logger.warning(f"[BG RENAME TASK - {task_id}] Duplicate NFC name '{f_normalized_nfc}' for raw names '{normalized_to_raw_map[f_normalized_nfc]}' and '{f_raw}'. Using last one.")
                    normalized_to_raw_map[f_normalized_nfc] = f_raw
            logger.info(f"[BG RENAME TASK - {task_id}] Raw files mapped. NFC keys: {list(normalized_to_raw_map.keys())}")
            if not normalized_to_raw_map:
                 logger.warning(f"[BG RENAME TASK - {task_id}] No files found in {base_image_path}")
        except OSError as e:
            logger.error(f"[BG RENAME TASK - {task_id}] Critical Error: Error listing files in {base_image_path}: {e}")
            results.append({"original_spec": "N/A", "status": "error", "message": f"Failed to list files. Error: {str(e)}"})
            error_count = len(student_list) # 모든 파일 처리 실패 간주
            logger.error(f"[BG RENAME TASK - {task_id}] 작업 중단. 파일 목록 읽기 실패.")
            return # 파일 목록 읽기 실패시 더 이상 진행 불가

        for item in student_list:
            if not isinstance(item, dict) or 'file_name' not in item:
                results.append({"original_spec": str(item), "status": "error", "message": "Invalid item format"})
                error_count += 1
                continue

            full_corrected_name_spec = unicodedata.normalize('NFC', item['file_name'])
            parts = full_corrected_name_spec.split('_', 1)
            if len(parts) < 2:
                results.append({"original_name_spec": full_corrected_name_spec, "status": "error", "message": "Spec does not contain '_' separator."})
                error_count += 1
                continue

            original_file_search_key_raw = parts[0]
            # 새 파일명도 일관되게 NFC 정규화
            new_full_filename_nfc = unicodedata.normalize('NFC', parts[1])
            
            original_file_search_key_base = original_file_search_key_raw
            for ext in known_extensions:
                if original_file_search_key_base.lower().endswith(ext.lower()):
                    original_file_search_key_base = original_file_search_key_base[:-len(ext)]
                    break
            original_file_search_key_base = unicodedata.normalize('NFC', original_file_search_key_base.strip())

            logger.info(f"[BG RENAME TASK - {task_id}] Processing: raw_key_from_spec='{original_file_search_key_raw}', final_search_key_base_nfc='{original_file_search_key_base}', new_name_nfc='{new_full_filename_nfc}'")

            found_files_details = []
            # 검색은 NFC 정규화된 파일명 목록 (normalized_to_raw_map의 key들)을 대상으로 수행
            for nfc_filename_from_dir in normalized_to_raw_map.keys():
                # 비교 대상인 디렉토리 파일의 베이스네임도 NFC 정규화된 상태에서 추출
                base_nfc_from_dir, _ = os.path.splitext(nfc_filename_from_dir)
                base_nfc_from_dir = base_nfc_from_dir.strip() # 이미 NFC 상태이므로 추가 정규화 불필요

                logger.debug(f"[BG RENAME TASK - {task_id}] Comparing DIR_base_nfc: '{base_nfc_from_dir}' (contains?) search_key_base_nfc: '{original_file_search_key_base}'")
                if original_file_search_key_base in base_nfc_from_dir:
                    raw_filename_matched = normalized_to_raw_map[nfc_filename_from_dir] # 실제 os.rename에 사용할 원본(raw) 파일명
                    found_files_details.append({
                        "nfc_name": nfc_filename_from_dir, 
                        "raw_name": raw_filename_matched, 
                        "base_nfc": base_nfc_from_dir
                    })
            
            logger.info(f"[BG RENAME TASK - {task_id}] For search_key_base_nfc '{original_file_search_key_base}', matched_raw_filenames: {[f['raw_name'] for f in found_files_details]}")
            
            if len(found_files_details) == 0:
                results.append({"search_key": original_file_search_key_base, "new_name": new_full_filename_nfc, "status": "error", "message": "Original file not found containing this key in its base name."})
                logger.warning(f"[BG RENAME TASK - {task_id}] Original file containing key '{original_file_search_key_base}' in its base name not found in {base_image_path}")
                error_count += 1
                continue
            elif len(found_files_details) > 1:
                ambiguous_files_log = [{'raw': f['raw_name'], 'nfc': f['nfc_name']} for f in found_files_details]
                results.append({"search_key": original_file_search_key_base, "new_name": new_full_filename_nfc, "status": "error", "message": f"Multiple files found: {ambiguous_files_log}. Ambiguous."})
                logger.warning(f"[BG RENAME TASK - {task_id}] Multiple files found for key '{original_file_search_key_base}': {ambiguous_files_log}. Ambiguous, skipping.")
                error_count += 1
                continue
            
            # 정확히 하나의 파일이 매칭됨
            # os.rename에는 ★원본(raw) 파일명★을 사용
            old_filename_raw_matched = found_files_details[0]['raw_name']
            old_file_path_raw = os.path.join(base_image_path, old_filename_raw_matched)
            
            # 새 파일 경로는 NFC 정규화된 이름 사용 (파일 시스템에 새로 기록되므로 일관된 형식 유지)
            new_file_path_nfc = os.path.join(base_image_path, new_full_filename_nfc)

            logger.info(f"[BG RENAME TASK - {task_id}] Attempting to rename RAW path: '{old_file_path_raw}' to NFC path: '{new_file_path_nfc}'")

            # rename 시도 전에 실제 원본(raw) 경로 존재 여부 확인
            if not os.path.exists(old_file_path_raw):
                logger.error(f"[BG RENAME TASK - {task_id}] CRITICAL: File '{old_file_path_raw}' (raw path for matched NFC name '{found_files_details[0]['nfc_name']}') not found on filesystem right before rename! Skipping.")
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "error", "message": "File disappeared or raw path mismatch."})
                error_count += 1
                continue

            # 자기 자신으로 이름 변경하는 경우 방지 (원본 raw 파일명과 NFC 새 파일명 비교)
            # 주의: old_filename_raw_matched는 raw, new_full_filename_nfc는 NFC 상태.
            # 비교를 위해서는 둘 다 NFC로 통일해서 비교해야 함.
            if unicodedata.normalize('NFC', old_filename_raw_matched) == new_full_filename_nfc:
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "skipped", "message": "New name is same as old name (after NFC normalization)."})
                logger.info(f"[BG RENAME TASK - {task_id}] Skipped renaming '{old_filename_raw_matched}' as new name '{new_full_filename_nfc}' is effectively identical.")
                skipped_count += 1
                continue

            try:
                os.rename(old_file_path_raw, new_file_path_nfc)
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "renamed"})
                logger.info(f"[BG RENAME TASK - {task_id}] Successfully renamed: '{old_file_path_raw}' -> '{new_file_path_nfc}'")
                renamed_count +=1
            except OSError as e:
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "error", "message": f"OS error during rename: {str(e)}"})
                # 에러 로그에 NFC 매칭 정보도 추가
                logger.error(f"[BG RENAME TASK - {task_id}] Error renaming RAW_PATH:'{old_file_path_raw}' to NFC_PATH:'{new_file_path_nfc}': {e}. Matched via NFC name: '{found_files_details[0]['nfc_name']}'")
                error_count += 1
        
        logger.info(f"[BG RENAME TASK - {task_id}] 파일명 변경 처리 완료. 성공: {renamed_count}, 실패: {error_count}, 스킵: {skipped_count}")

    except Exception as e:
        logger.error(f"[BG RENAME TASK - {task_id}] 백그라운드 작업 중 전역 예외 발생: {traceback.format_exc()}")
        # 부분 성공/실패 결과가 있다면 results에 기록되었을 것이고, Kafka 등으로 보낼 수 있음




@app.route('/generate-report', methods=['POST'])
def generate_report():
    data = request.get_json(force=True)

    subject = data.get("subject")
    responses = data.get("responses", [])

    # 1. 점수 수집
    scores = [r.get("totalScore", 0) for r in responses]

    # 2. 통계 계산
    mean_score = np.mean(scores) if scores else 0
    std_dev = np.std(scores) if scores else 0

    # 3. 히스토그램 생성 (세로축: 인원 수, 가로축: 점수)
    plt.figure(figsize=(10, 6))
    # scores가 비어있거나 모든 점수가 동일한 경우 hist가 에러를 발생시킬 수 있음
    if not scores or len(set(scores)) == 1:
        # 단일 값 또는 빈 값에 대한 처리: bins를 1로 설정하거나, hist 대신 다른 시각화
        if scores: # 모든 점수가 같은 경우
             plt.hist(scores, bins=1, color='skyblue', edgecolor='black')
        else: # scores가 빈 경우
            plt.hist([], bins=10, color='skyblue', edgecolor='black') # 빈 히스토그램
    else:
        plt.hist(scores, bins=10, color='skyblue', edgecolor='black')

    plt.xlabel('Score')
    plt.ylabel('Number of Students')
    plt.title(f'Score Distribution - {subject if subject else "Unknown Subject"}')
    plt.grid(True)

    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # 평균, 표준편차 텍스트
    stat_text = f"Mean: {mean_score:.2f}, Std Dev: {std_dev:.2f}"
    plt.text(0.95, 0.95, stat_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle="round,pad=0.3", edgecolor='gray', facecolor='white'))

    plt.tight_layout()

    # 4. 그래프를 이미지로 저장
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close() # 그래프 생성 후 리소스 해제

    # 5. PDF 생성
    pdf_buf = io.BytesIO()
    # reportlab에서 한글 사용을 위해 폰트 설정 (필요한 경우)
    # from reportlab.pdfbase import pdfmetrics
    # from reportlab.pdfbase.ttfonts import TTFont
    # NanumGothic.ttf 와 같은 한글 폰트 파일이 필요합니다.
    # 실제 경로에 맞게 수정해야 합니다.
    # try:
    #     pdfmetrics.registerFont(TTFont('NanumGothic', '/usr/share/fonts/truetype/nanum/NanumGothic.ttf')) # 예시 경로
    #     font_name = 'NanumGothic'
    # except: # 폰트 로드 실패 시 기본 폰트 사용
    #     app.logger.warning("NanumGothic font not found. Using default font for PDF.")
    #     font_name = 'Helvetica'
    
    # 임시로 기본 폰트 사용
    font_name = 'Helvetica'

    c = canvas.Canvas(pdf_buf, pagesize=letter)
    
    # 제목 폰트 설정 및 그리기
    c.setFont(font_name, 16)
    subject_text = f"Subject: {subject if subject else 'Unknown Subject'}"
    c.drawString(100, 750, subject_text)

    # 통계 정보 폰트 설정 및 그리기
    c.setFont(font_name, 12)
    stats_string = f"Mean: {mean_score:.2f}, Standard Deviation: {std_dev:.2f}"
    c.drawString(100, 720, stats_string)

    # 이미지 삽입 (임시 파일 생성 없이 BytesIO 직접 사용 가능성 확인)
    # ReportLab은 BytesIO에서 직접 이미지를 로드할 수 있습니다.
    img_buf.seek(0) # BytesIO 포인터를 다시 처음으로
    # ReportLab의 ImageReader는 BytesIO 객체를 직접 받을 수 있습니다.
    from reportlab.lib.utils import ImageReader
    img_reader = ImageReader(img_buf)
    c.drawImage(img_reader, 100, 350, width=400, height=300) # x, y, width, height

    c.showPage()
    c.save()
    pdf_buf.seek(0)

    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{secure_filename(subject if subject else 'report')}_report.pdf" # 파일명 보안 처리
    )

@app.route('/get-student-image', methods=['GET'])
def get_student_image():
    try:
        subject_name = request.args.get('subject')
        student_id_query = request.args.get('student_id')
        # image_folder_name 파라미터 제거

        if not subject_name:
            return jsonify({"error": "Missing 'subject' query parameter"}), 400
        if not student_id_query:
            return jsonify({"error": "Missing 'student_id' query parameter"}), 400
        # image_folder_name 파라미터 검사 제거

        app.logger.info(f"[get-student-image] Request for subject: '{subject_name}', student_id: '{student_id_query}'") # 로깅 수정

        # 과목명으로 기본 경로 설정
        subject_name_for_path = subject_name 
        subject_path = os.path.join(APP_ROOT, subject_name_for_path)

        if not os.path.isdir(subject_path):
            app.logger.error(f"[get-student-image] Subject base path not found: {subject_path}")
            return jsonify({"error": f"Directory for subject '{subject_name_for_path}' not found."}), 404

        # 과목 폴더 내의 하위 디렉토리(압축 해제된 이미지 폴더) 찾기 - 이전 로직 복원
        try:
            subdirectories = [d for d in os.listdir(subject_path) 
                              if os.path.isdir(os.path.join(subject_path, d)) and 
                              d != 'debug_cropped_images' and not d.startswith('.')]
        except OSError as e:
            app.logger.error(f"[get-student-image] Error listing subdirectories in {subject_path}: {e}")
            return jsonify({"error": f"Could not read subject directory contents for '{subject_name_for_path}'."}), 500

        if len(subdirectories) == 0:
            app.logger.error(f"[get-student-image] No image data subdirectories found in {subject_path} for subject '{subject_name_for_path}'.")
            return jsonify({"error": f"No processed image folder found for subject '{subject_name_for_path}'."}), 404
        elif len(subdirectories) > 1:
            app.logger.warning(f"[get-student-image] Multiple image data subdirectories found in {subject_path}: {subdirectories}. Using the first one: {subdirectories[0]}")
            # 또는 필요시 에러 처리:
            # return jsonify({"error": f"Multiple processed image folders found for subject '{subject_name_for_path}'. Cannot determine target."}), 409
        
        target_image_folder_name = subdirectories[0] # 스캔을 통해 찾은 폴더명 사용
        base_image_path = os.path.join(subject_path, target_image_folder_name)
        app.logger.info(f"[get-student-image] Target image path: {base_image_path} (determined by scanning)")

        if not os.path.isdir(base_image_path): # 이 검사는 여전히 유효
            app.logger.error(f"[get-student-image] Determined image folder is not a directory: {base_image_path}")
            return jsonify({"error": f"Determined image folder '{target_image_folder_name}' for subject '{subject_name_for_path}' is not a valid directory."}), 500

        normalized_student_id_query = unicodedata.normalize('NFC', student_id_query)
        found_image_path = None

        try:
            for filename_raw in os.listdir(base_image_path):
                if os.path.isfile(os.path.join(base_image_path, filename_raw)):
                    filename_nfc = unicodedata.normalize('NFC', filename_raw)
                    base_name_nfc, ext = os.path.splitext(filename_nfc)
                    
                    if '_' in base_name_nfc:
                        parts = base_name_nfc.split('_')
                        file_student_id_part = parts[-1]
                        
                        if file_student_id_part == normalized_student_id_query:
                            found_image_path = os.path.join(base_image_path, filename_raw) # 원본 파일명으로 경로 생성
                            app.logger.info(f"[get-student-image] Found matching image: {found_image_path}")
                            break 
            
            if found_image_path:
                return send_file(found_image_path) # mimetype은 send_file이 자동 감지 시도
            else:
                app.logger.warning(f"[get-student-image] Image for student_id '{student_id_query}' not found in {base_image_path}")
                return jsonify({"error": f"Image for student ID '{student_id_query}' not found."}), 404

        except OSError as e:
            app.logger.error(f"[get-student-image] Error reading image directory {base_image_path}: {e}")
            return jsonify({"error": "Error accessing image files."}), 500

    except Exception as e:
        app.logger.error(f"[get-student-image] Unexpected error: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, World", 200

if __name__ == '__main__':
    # Spring과의 통신을 위해 0.0.0.0으로 호스트를 설정하고, 지정된 포트(예: 8080)를 사용합니다.
    # Docker 환경에서는 이 포트가 외부로 노출됩니다.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True는 개발 중에만 사용

