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
from datetime import datetime # Kafka 메시지 타임스탬프용
import requests # Spring 서버 통신용
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

# Algorithm.OCR 모듈 import
from answer_recognition.main import preprocess_answer_sheet, recognize_answer_sheet_data

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

    if producer is not None:
        try:
            # Kafka 브로커와의 연결 상태를 확인하기 위해 빈 메시지를 전송
            producer.send('low-confidence-images', value={"status": "check"})
            app.logger.info("Kafka broker is connected and healthy.")
            return jsonify({"status": "healthy", "message": "Kafka broker is connected and healthy."}), 200
        except Exception as e:
            app.logger.error(f"Kafka broker connection check failed: {e}")
    else:
        app.logger.warning("Kafka producer is not initialized. Skipping Kafka health check.")

    
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

def send_spring_notification(action, subject_name, additional_data=None, request_origin=None):
    """Spring 서버에 알림을 보내는 함수 - 요청을 보낸 곳으로 callback"""
    try:
        if not request_origin:
            app.logger.info(f"[Spring 알림] callback할 origin이 없어 알림을 건너뜁니다. Status: {action}, Subject: {subject_name}")
            return
        
        # Origin에서 callback URL 구성 - Spring Boot 표준 API 경로로 수정
        callback_url = f"{request_origin}/api/ocr/callback"  # 더 명확한 엔드포인트명
        
        payload = {
            "status": action,  # "pending" 또는 "DONE"
            "subject": subject_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if additional_data:
            payload.update(additional_data)
        
        app.logger.info(f"[Spring 알림] {action} 신호를 요청 origin으로 전송: {callback_url}")
        app.logger.debug(f"[Spring 알림] Payload: {payload}")  # 디버깅용 로그 추가
        
        try:
            response = requests.post(callback_url, json=payload, timeout=10)
            app.logger.info(f"[Spring 알림] 응답 상태: {response.status_code}")
            
            # 응답 내용도 로깅 (디버깅 시 유용)
            if response.status_code != 200:
                app.logger.warning(f"[Spring 알림] 비정상 응답: {response.text}")
            else:
                app.logger.info(f"[Spring 알림] 성공적으로 전송됨")
                
        except requests.exceptions.Timeout:
            app.logger.warning(f"[Spring 알림] 타임아웃 발생 (10초): {callback_url}")
        except requests.exceptions.ConnectionError:
            app.logger.warning(f"[Spring 알림] 연결 실패: {callback_url}")
        except requests.exceptions.RequestException as req_error:
            app.logger.warning(f"[Spring 알림] HTTP 요청 실패: {req_error}")
        except Exception as general_error:
            app.logger.error(f"[Spring 알림] 일반 오류: {general_error}")
        
    except Exception as e:
        app.logger.error(f"Spring 알림 전송 실패 ({action}): {e}")
        app.logger.error(f"Spring 알림 전송 실패 상세: {traceback.format_exc()}")

def background_answer_recognition_task(subject_name, student_id_update_data, answer_key_data, parent_logger, request_origin):
    """백그라운드에서 답안 인식을 수행하는 함수"""
    logger = parent_logger
    task_id = f"answer-recognition-{subject_name}-{uuid.uuid4().hex[:8]}"
    
    try:
        logger.info(f"[BG ANSWER TASK - {task_id}] 작업 시작")
        
        # 작업 상태 등록
        current_tasks[subject_name] = {"status": "pending", "task_id": task_id}
        
        # Spring에 처리 시작 알림
        send_spring_notification("pending", subject_name, {"task_id": task_id}, request_origin)
        
        # 기존 답안 인식 로직 수행
        student_list = student_id_update_data.get('student_list')
        subject_name_for_path = subject_name if subject_name else uuid.uuid4().hex
        subject_path = os.path.join(APP_ROOT, subject_name_for_path)

        if not os.path.isdir(subject_path):
            logger.error(f"Subject path not found: {subject_path}")
            current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": "Subject directory not found"}
            send_spring_notification("DONE", subject_name, {
                "task_id": task_id, 
                "status": "error", 
                "message": "Subject directory not found"
            }, request_origin)
            return

        # 하위 디렉토리 찾기
        subdirectories = [d for d in os.listdir(subject_path) if os.path.isdir(os.path.join(subject_path, d))]
        
        if len(subdirectories) != 1:
            logger.error(f"Expected 1 subdirectory, found {len(subdirectories)}")
            current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": f"Invalid subdirectory count: {len(subdirectories)}"}
            send_spring_notification("DONE", subject_name, {
                "task_id": task_id,
                "status": "error", 
                "message": f"Invalid subdirectory count: {len(subdirectories)}"
            }, request_origin)
            return

        target_zip_folder_name = subdirectories[0]
        base_image_path = os.path.join(subject_path, target_zip_folder_name)
        logger.info(f"Target base image path: {base_image_path}")

        # 파일명 변경 작업 (동기적으로 수행)
        logger.info(f"[BG ANSWER TASK - {task_id}] 파일명 변경 시작")
        current_tasks[subject_name] = {"status": "processing", "task_id": task_id, "message": "파일명 변경 중"}
        background_rename_files_task(subject_name, student_list, base_image_path, logger)
        logger.info(f"[BG ANSWER TASK - {task_id}] 파일명 변경 완료")

        # 답안 인식 로직 수행
        logger.info(f"[BG ANSWER TASK - {task_id}] 답안 인식 시작")
        current_tasks[subject_name] = {"status": "processing", "task_id": task_id, "message": "답안 인식 중"}
        
        dir_path = os.path.join(APP_ROOT, subject_name, subject_name)
        
        if not os.path.exists(dir_path):
            logger.error(f"디렉토리를 찾을 수 없습니다: {dir_path}")
            current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": f"Directory not found: {dir_path}"}
            send_spring_notification("DONE", subject_name, {
                "task_id": task_id,
                "status": "error",
                "message": f"Directory not found: {dir_path}"
            }, request_origin)
            return

        # 이미지 파일 목록 추출
        image_extensions = ['.jpg', '.jpeg', '.png']
        image_files = []
        for ext in image_extensions:
            image_files.extend([f for f in os.listdir(dir_path) if f.lower().endswith(ext)])

        if not image_files:
            logger.warning(f"이미지 파일을 찾을 수 없습니다: {dir_path}")
            current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": "No image files found"}
            send_spring_notification("DONE", subject_name, {
                "task_id": task_id,
                "status": "error",
                "message": "No image files found"
            }, request_origin)
            return

        logger.info(f"발견된 이미지 파일 {len(image_files)}개")

        # 답안 인식 수행
        errors = []
        failure_json = {
            "subject": subject_name,
            "images": []
        }

        # tail_question_counts 계산
        from collections import defaultdict
        def extract_tail_question_counts(answer_key_data: dict) -> dict:
            tail_question_counts = defaultdict(int)
            for q in answer_key_data.get("questions", []):
                qn = str(q["question_number"])
                tail_question_counts[qn] += 1
            return dict(tail_question_counts)
        
        tail_question_counts = extract_tail_question_counts(answer_key_data)

        # 각 이미지 처리
        processed_count = 0
        for image_file in image_files:
            try:
                image_path = os.path.join(dir_path, image_file)
                logger.info(f"처리 중: {image_file}")
                
                # 진행 상황 업데이트
                current_tasks[subject_name] = {"status": "processing", "task_id": task_id, "message": f"처리 중: {processed_count+1}/{len(image_files)}"}

                # 1. 전처리
                processed_crops = preprocess_answer_sheet(image_path, answer_key_data)
                if not processed_crops:
                    logger.warning(f"전처리 결과가 없음: {image_file}")
                    errors.append({"file": image_file, "error": "No crops from preprocessing"})
                    continue

                # 2. 인식
                recognition_result = recognize_answer_sheet_data(processed_crops, answer_key_data, tail_question_counts)

                # Kafka로 결과 전송
                answer_json = recognition_result.get("answer_json", {})
                if producer:
                    try:
                        producer.send('student-responses', answer_json)
                        producer.flush()
                    except Exception as kafka_error:
                        logger.error(f"Kafka 전송 실패 ({image_file}): {kafka_error}")

                # failure_json 업데이트
                failure_images = recognition_result.get("failure_json", [])
                failure_json["images"].extend(failure_images)

                # 결과 저장
                answer_json_filename = os.path.join(dir_path, f"{os.path.splitext(image_file)[0]}_answers.json")
                with open(answer_json_filename, 'w', encoding='utf-8') as f:
                    json.dump(answer_json, f, ensure_ascii=False, indent=4)

                processed_count += 1
                logger.info(f"처리 완료: {image_file} ({processed_count}/{len(image_files)})")

            except Exception as e:
                logger.error(f"이미지 처리 중 오류 ({image_file}): {traceback.format_exc()}")
                errors.append({"file": image_file, "error": str(e)})

        # failure_json 저장 및 Kafka 전송
        failure_json_filename = os.path.join(APP_ROOT, subject_name, "failure.json")
        with open(failure_json_filename, 'w', encoding='utf-8') as f:
            json.dump(failure_json, f, ensure_ascii=False, indent=4)

        if producer:
            try:
                producer.send('low-confidence-images', failure_json)
                producer.flush()
            except Exception as kafka_error:
                logger.error(f"Failure JSON Kafka 전송 실패: {kafka_error}")

        # 작업 완료 상태 업데이트
        current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": f"완료: {processed_count}/{len(image_files)} 처리됨"}

        # Spring에 완료 알림
        send_spring_notification("DONE", subject_name, {
            "task_id": task_id,
            "status": "success",
            "processed_files": processed_count,
            "total_files": len(image_files),
            "errors": len(errors)
        }, request_origin)

        logger.info(f"[BG ANSWER TASK - {task_id}] 작업 완료. 처리: {processed_count}/{len(image_files)}, 오류: {len(errors)}")

    except Exception as e:
        logger.error(f"[BG ANSWER TASK - {task_id}] 백그라운드 작업 중 예외 발생: {traceback.format_exc()}")
        current_tasks[subject_name] = {"status": "DONE", "task_id": task_id, "message": f"오류 발생: {str(e)}"}
        send_spring_notification("DONE", subject_name, {
            "task_id": task_id,
            "status": "error",
            "message": str(e)
        }, request_origin)

@app.route('/recognize/answer', methods=['POST'])
def recognize_answer_endpoint():
    """2차 답안 인식 엔드포인트: 비동기 처리로 즉시 응답 반환"""
    
    try:
        # JSON 파싱
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "No JSON payload provided"}), 400

        student_id_update_data = request_data.get('studentIdUpdateDto')
        if not student_id_update_data:
            return jsonify({"error": "Missing 'studentIdUpdateDto' in JSON payload"}), 400

        answer_key_data = request_data.get('examDto')
        if not answer_key_data:
            return jsonify({"error": "Missing 'examDto' in JSON payload"}), 400

        subject_name = student_id_update_data.get('subject')
        if not subject_name:
            return jsonify({"error": "Missing 'subject' in studentIdUpdateDto"}), 400

        student_list = student_id_update_data.get('student_list')
        if not student_list:
            return jsonify({"error": "Missing 'student_list' in studentIdUpdateDto"}), 400

        # 요청 origin 추출 - 개선된 버전
        # Spring 서버에서 callback을 받을 주소를 명시적으로 추출
        request_origin = request.headers.get('X-Forwarded-For') or request.headers.get('Origin')
        if not request_origin:
            # Host 헤더에서 추출하되, 프로토콜 자동 감지
            host = request.headers.get('Host', 'localhost:8080')
            # HTTPS 여부 확인 (X-Forwarded-Proto 또는 기본값)
            is_https = request.headers.get('X-Forwarded-Proto') == 'https' or request.is_secure
            protocol = 'https' if is_https else 'http'
            request_origin = f"{protocol}://{host}"

        app.logger.info(f"[recognize_answer] 요청 origin: {request_origin}")

        app.logger.info(f"[recognize_answer] 비동기 처리 시작 - subject: {subject_name}")

        # 백그라운드 스레드 시작
        task_id = f"answer-{subject_name}-{uuid.uuid4().hex[:8]}"
        thread = threading.Thread(
            target=background_answer_recognition_task,
            args=(subject_name, student_id_update_data, answer_key_data, app.logger, request_origin),
            name=f"AnswerRecognition-{task_id}"
        )
        thread.start()

        app.logger.info(f"백그라운드 답안 인식 스레드 시작됨: {thread.name}")

        # 즉시 응답 반환
        return jsonify({
            "status": "processing_started",
            "message": "Answer recognition process started in background",
            "task_id": task_id,
            "subject": subject_name
        }), 202

    except Exception as e:
        app.logger.error(f"recognize_answer_endpoint 예외 발생: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

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

    # --- Matplotlib 설정 ---
    font_path = os.path.join(APP_ROOT, 'font', 'NanumGothic.ttf')
    font_prop = None
    try:
        from matplotlib import font_manager
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Font file not found at {font_path}")
        
        font_prop = font_manager.FontProperties(fname=font_path)
        plt.rcParams['axes.unicode_minus'] = False
        app.logger.info(f"Matplotlib font properties loaded from {font_path}")
    except Exception as e:
        app.logger.warning(f"Failed to load Matplotlib font: {e}. Using default font.")

    # 3. 히스토그램 생성
    plt.figure(figsize=(10, 6))
    if not scores or len(set(scores)) == 1:
        if scores:
             plt.hist(scores, bins=1, color='skyblue', edgecolor='black')
        else:
            plt.hist([], bins=10, color='skyblue', edgecolor='black')
    else:
        plt.hist(scores, bins=10, color='skyblue', edgecolor='black')

    # 폰트 적용하여 라벨 설정
    plt.xlabel('점수', fontproperties=font_prop)
    plt.ylabel('학생 수', fontproperties=font_prop)
    plt.title(f'점수 분포 - {subject if subject else "과목 없음"}', fontproperties=font_prop)
    plt.grid(True)
    plt.gca().yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    
    stat_text = f"평균: {mean_score:.2f}, 표준편차: {std_dev:.2f}"
    plt.text(0.95, 0.95, stat_text, transform=plt.gca().transAxes,
             fontsize=10, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle="round,pad=0.3", edgecolor='gray', facecolor='white'),
             fontproperties=font_prop)
    plt.tight_layout()

    # 4. 그래프를 이미지로 저장
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close()

    # --- PDF 생성 (ReportLab) ---
    pdf_buf = io.BytesIO()
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    
    font_name_pdf = 'Helvetica' # 기본 폰트
    try:
        if not os.path.exists(font_path):
             raise FileNotFoundError(f"Font file not found at {font_path}")
        pdfmetrics.registerFont(TTFont('NanumGothic', font_path))
        font_name_pdf = 'NanumGothic'
        app.logger.info("ReportLab font set to 'NanumGothic'")
    except Exception as e:
        app.logger.warning(f"Failed to set ReportLab font: {e}. Using default font.")

    c = canvas.Canvas(pdf_buf, pagesize=letter)
    c.setFont(font_name_pdf, 16)
    c.drawString(100, 750, f"과목: {subject if subject else '과목 없음'}")
    c.setFont(font_name_pdf, 12)
    c.drawString(100, 720, f"평균: {mean_score:.2f}, 표준편차: {std_dev:.2f}")

    from reportlab.lib.utils import ImageReader
    img_reader = ImageReader(img_buf)
    c.drawImage(img_reader, 100, 350, width=400, height=300)

    c.showPage()
    c.save()
    pdf_buf.seek(0)

    return send_file(
        pdf_buf,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{secure_filename(subject if subject else 'report')}_report.pdf"
    )

@app.route('/get-student-image', methods=['POST'])
def get_student_image():
    try:
        data = request.get_json()
        subject_name = data.get('subject')
        student_id_query = data.get('student_id')

        if not subject_name:
            return jsonify({"error": "Missing 'subject' in JSON payload"}), 400
        if not student_id_query:
            return jsonify({"error": "Missing 'student_id' in JSON payload"}), 400

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
                # 이미지 전송 전 디버깅 로그
                file_size = os.path.getsize(found_image_path)
                app.logger.info(f"[get-student-image] Preparing to send image: {found_image_path} (size: {file_size} bytes)")
                print(f"[DEBUG] Sending image for student_id '{student_id_query}': {found_image_path} ({file_size} bytes)")
                
                try:
                    response = send_file(found_image_path) # mimetype은 send_file이 자동 감지 시도
                    app.logger.info(f"[get-student-image] Image successfully sent for student_id '{student_id_query}'")
                    print(f"[DEBUG] Image successfully sent for student_id '{student_id_query}'")
                    return response
                except Exception as send_error:
                    app.logger.error(f"[get-student-image] Error sending image file: {send_error}")
                    print(f"[DEBUG ERROR] Failed to send image: {send_error}")
                    return jsonify({"error": f"Failed to send image file: {str(send_error)}"}), 500
            else:
                app.logger.warning(f"[get-student-image] Image for student_id '{student_id_query}' not found in {base_image_path}")
                return jsonify({"error": f"Image for student ID '{student_id_query}' not found."}), 404

        except OSError as e:
            app.logger.error(f"[get-student-image] Error reading image directory {base_image_path}: {e}")
            return jsonify({"error": "Error accessing image files."}), 500

    except Exception as e:
        app.logger.error(f"[get-student-image] Unexpected error: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    
@app.route('/test-spring-notification', methods=['POST'])
def test_spring_notification():
    """Spring 알림 테스트용 엔드포인트"""
    try:
        data = request.get_json()
        status = data.get('status', 'pending')  # action 대신 status 사용
        subject_name = data.get('subject', 'test-subject')
        
        # 요청 origin 추출 (동일한 로직 사용)
        request_origin = request.headers.get('X-Forwarded-For') or request.headers.get('Origin')
        if not request_origin:
            host = request.headers.get('Host', 'localhost:8080')
            is_https = request.headers.get('X-Forwarded-Proto') == 'https' or request.is_secure
            protocol = 'https' if is_https else 'http'
            request_origin = f"{protocol}://{host}"
        
        app.logger.info(f"[테스트] Spring 알림 테스트 - Origin: {request_origin}, Status: {status}")
        
        # 테스트 알림 전송
        send_spring_notification(status, subject_name, {
            "test": True,
            "task_id": "test-task-123"
        }, request_origin)
        
        return jsonify({
            "status": "success",
            "message": "Spring 알림 테스트 전송 완료",
            "target_origin": request_origin,
            "sent_status": status,
            "subject": subject_name
        }), 200
        
    except Exception as e:
        app.logger.error(f"Spring 알림 테스트 실패: {traceback.format_exc()}")
        return jsonify({"error": f"테스트 실패: {str(e)}"}), 500
    
@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, World", 200

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
                        logger.warning(f"[BG RENAME TASK - {task_id}] Duplicate NFC name '{f_normalized_nfc}' for raw names '{normalized_to_raw_map[f_normalized_nfc]}' and '{f_raw}'. Using last one.")
                    normalized_to_raw_map[f_normalized_nfc] = f_raw
            logger.info(f"[BG RENAME TASK - {task_id}] Raw files mapped. NFC keys: {list(normalized_to_raw_map.keys())}")
            if not normalized_to_raw_map:
                 logger.warning(f"[BG RENAME TASK - {task_id}] No files found in {base_image_path}")
        except OSError as e:
            logger.error(f"[BG RENAME TASK - {task_id}] Critical Error: Error listing files in {base_image_path}: {e}")
            results.append({"original_spec": "N/A", "status": "error", "message": f"Failed to list files. Error: {str(e)}"})
            error_count = len(student_list)
            logger.error(f"[BG RENAME TASK - {task_id}] 작업 중단. 파일 목록 읽기 실패.")
            return

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
            new_full_filename_nfc = unicodedata.normalize('NFC', parts[1])
            
            original_file_search_key_base = original_file_search_key_raw
            for ext in known_extensions:
                if original_file_search_key_base.lower().endswith(ext.lower()):
                    original_file_search_key_base = original_file_search_key_base[:-len(ext)]
                    break
            original_file_search_key_base = unicodedata.normalize('NFC', original_file_search_key_base.strip())

            logger.info(f"[BG RENAME TASK - {task_id}] Processing: raw_key_from_spec='{original_file_search_key_raw}', final_search_key_base_nfc='{original_file_search_key_base}', new_name_nfc='{new_full_filename_nfc}'")

            found_files_details = []
            for nfc_filename_from_dir in normalized_to_raw_map.keys():
                base_nfc_from_dir, _ = os.path.splitext(nfc_filename_from_dir)
                base_nfc_from_dir = base_nfc_from_dir.strip()

                logger.debug(f"[BG RENAME TASK - {task_id}] Comparing DIR_base_nfc: '{base_nfc_from_dir}' (contains?) search_key_base_nfc: '{original_file_search_key_base}'")
                if original_file_search_key_base in base_nfc_from_dir:
                    raw_filename_matched = normalized_to_raw_map[nfc_filename_from_dir]
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
            
            old_filename_raw_matched = found_files_details[0]['raw_name']
            old_file_path_raw = os.path.join(base_image_path, old_filename_raw_matched)
            new_file_path_nfc = os.path.join(base_image_path, new_full_filename_nfc)

            logger.info(f"[BG RENAME TASK - {task_id}] Attempting to rename RAW path: '{old_file_path_raw}' to NFC path: '{new_file_path_nfc}'")

            if not os.path.exists(old_file_path_raw):
                logger.error(f"[BG RENAME TASK - {task_id}] CRITICAL: File '{old_file_path_raw}' not found on filesystem right before rename! Skipping.")
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "error", "message": "File disappeared or raw path mismatch."})
                error_count += 1
                continue

            if unicodedata.normalize('NFC', old_filename_raw_matched) == new_full_filename_nfc:
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "skipped", "message": "New name is same as old name (after NFC normalization)."})
                logger.info(f"[BG RENAME TASK - {task_id}] Skipped renaming '{old_filename_raw_matched}' as new name '{new_full_filename_nfc}' is effectively identical.")
                skipped_count += 1
                continue

            try:
                os.rename(old_file_path_raw, new_file_path_nfc)
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "renamed"})
                logger.info(f"[BG RENAME TASK - {task_id}] Successfully renamed: '{old_file_path_raw}' -> '{new_file_path_nfc}'")
                renamed_count+=1
            except OSError as e:
                results.append({"original_name_raw": old_filename_raw_matched, "new_name": new_full_filename_nfc, "status": "error", "message": f"OS error during rename: {str(e)}"})
                logger.error(f"[BG RENAME TASK - {task_id}] Error renaming RAW_PATH:'{old_file_path_raw}' to NFC_PATH:'{new_file_path_nfc}': {e}. Matched via NFC name: '{found_files_details[0]['nfc_name']}'")
                error_count += 1
        
        logger.info(f"[BG RENAME TASK - {task_id}] 파일명 변경 처리 완료. 성공: {renamed_count}, 실패: {error_count}, 스킵: {skipped_count}")

    except Exception as e:
        logger.error(f"[BG RENAME TASK - {task_id}] 백그라운드 작업 중 전역 예외 발생: {traceback.format_exc()}")

# 간단한 작업 상태 추적
current_tasks = {}  # {"subject": {"status": "pending|processing|DONE", "task_id": "xxx"}}

@app.route('/get-status', methods=['POST'])
def get_status():
    """Spring에서 작업 상태를 조회하는 엔드포인트"""
    try:
        data = request.get_json()
        subject = data.get('subject')
        
        if not subject:
            return jsonify({"error": "subject가 필요합니다"}), 400
        
        # 해당 과목의 현재 작업 상태 확인
        if subject in current_tasks:
            task_info = current_tasks[subject]
            return jsonify({
                "subject": subject,
                "status": task_info["status"],  # "pending" 또는 "processing" 또는 "DONE"
                "task_id": task_info.get("task_id"),
                "message": task_info.get("message", "")
            }), 200
        else:
            return jsonify({
                "subject": subject,
                "status": "not_found",
                "message": "해당 과목의 작업이 없습니다"
            }), 404
            
    except Exception as e:
        return jsonify({"error": f"상태 조회 실패: {str(e)}"}), 500

if __name__ == '__main__':
    # Spring과의 통신을 위해 0.0.0.0으로 호스트를 설정하고, 지정된 포트(예: 8080)를 사용합니다.
    # Docker 환경에서는 이 포트가 외부로 노출됩니다.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True는 개발 중에만 사용

