import sys # 경로 추가를 위해 import
from flask import Flask, request, jsonify, current_app
import os
import tempfile
import traceback
import zipfile # decompression 모듈 내부에서 사용하지만, 여기서도 파일 타입 체크 등에 사용 가능
import pandas as pd # XLSX 처리용
from werkzeug.utils import secure_filename # 안전한 파일명 생성
import uuid # UUID 추가
import shutil # 백그라운드 작업에서 임시 폴더 삭제용
import json # KafkaProducer value_serializer에서 사용되므로 필요, Flask jsonify와는 다름

import threading
from kafka import KafkaProducer
# Flask의 jsonify와 이름 충돌을 피하기 위해 json 모듈은 보통 그대로 사용합니다.
# value_serializer에서 json.dumps를 사용하므로 import json은 필요합니다.

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

# Kafka 프로듀서 설정 (Flask 초기화 시에 생성해두는 것을 권장)
# bootstrap_servers는 실제 환경에 맞게 수정해야 합니다.
producer = None
try:
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092', # TODO: 실제 Kafka 서버 주소로 변경!
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    app.logger.info("Kafka Producer initialized successfully.")
except Exception as e:
    app.logger.error(f"Failed to initialize Kafka Producer: {e}. Background tasks might not send Kafka messages.")
    # Kafka 연결 실패 시 프로듀서가 None으로 유지됩니다.
    # 백그라운드 작업에서 producer 사용 전 None 체크 필요.

# 파일 업로드를 위한 임시 디렉토리 생성 방식을 Flask app context와 함께 관리
# @app.before_first_request
# def setup_temp_dir():
# if not hasattr(current_app, 'UPLOAD_FOLDER') or not os.path.exists(current_app.UPLOAD_FOLDER):
#         current_app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp(prefix='ocr_flask_uploads_')
#         print(f"임시 업로드 폴더 생성: {current_app.config['UPLOAD_FOLDER']}")

# 위 방식 대신, 앱 초기화 시점에 생성
UPLOAD_FOLDER_BASE = os.path.join(tempfile.gettempdir(), 'ocr_flask_uploads')
os.makedirs(UPLOAD_FOLDER_BASE, exist_ok=True)
app.config['UPLOAD_FOLDER_BASE'] = UPLOAD_FOLDER_BASE

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

def background_task(subject_name, zip_path, xlsx_path, extracted_images_path, session_temp_dir, parent_logger):
    logger = parent_logger # 전달받은 로거 사용
    try:
        logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] 작업 시작.")
        # 4. 압축 해제
        if not extract_archive(zip_path, extracted_images_path):
            logger.error(f"[BG TASK - {os.path.basename(session_temp_dir)}] 압축 해제 실패: {zip_path}")
            return
        logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] 압축 해제 완료: {zip_path} -> {extracted_images_path}")

        # 5. XLSX 파싱
        student_numbers_from_xlsx = []
        if os.path.exists(xlsx_path):
            try:
                student_numbers_from_xlsx = parsing_xlsx(xlsx_file_path=xlsx_path)
                logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] XLSX 파싱 완료. 학번 {len(student_numbers_from_xlsx)}개 로드.")
            except Exception as e:
                logger.error(f"[BG TASK - {os.path.basename(session_temp_dir)}] XLSX 파싱 오류 ({xlsx_path}): {e}")
        else:
            logger.warning(f"[BG TASK - {os.path.basename(session_temp_dir)}] XLSX 파일 없음: {xlsx_path}")

        # 6. 학번 인식
        logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] 학번 인식 모듈 호출...")
        result_from_module = process_student_ids(extracted_images_path, student_numbers_from_xlsx)
        result_from_module["subject"] = subject_name
        # 1차 인식 결과에 session_id 추가 (추후 상태 추적 또는 결과 매칭에 사용 가능)
        result_from_module["session_id"] = os.path.basename(session_temp_dir)
        logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] 학번 인식 완료.")

        # 7. Kafka로 결과 전송
        if producer:
            try:
                topic_name = "student-id-recognition-result" # 필요시 토픽명 변경
                producer.send(topic_name, result_from_module)
                producer.flush()
                logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] Kafka 전송 완료. Topic: {topic_name}")
            except Exception as e:
                logger.error(f"[BG TASK - {os.path.basename(session_temp_dir)}] Kafka 메시지 전송 실패: {e}")
        else:
            logger.error(f"[BG TASK - {os.path.basename(session_temp_dir)}] Kafka Producer not available. Skipping message send.")

    except Exception as e:
        logger.error(f"[BG TASK - {os.path.basename(session_temp_dir)}] 백그라운드 작업 중 예외 발생: {traceback.format_exc()}")
    finally:
        if os.path.exists(session_temp_dir):
            try:
                shutil.rmtree(session_temp_dir)
                logger.info(f"[BG TASK - {os.path.basename(session_temp_dir)}] 세션 임시 폴더 삭제 완료.")
            except Exception as e:
                logger.warning(f"[BG TASK - {os.path.basename(session_temp_dir)}] 세션 임시 폴더 삭제 실패: {e}")

@app.route('/recognize/student_id', methods=['POST'])
def recognize_student_id_endpoint():
    session_temp_dir = None # finally 또는 except에서 사용하기 위해 try 바깥에 선언
    try:
        subject_name = request.form.get('subject')
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

        session_temp_dir = tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER_BASE'])
        app.logger.info(f"세션 임시 폴더 생성: {session_temp_dir} (ID: {os.path.basename(session_temp_dir)})")

        original_zip_filename = zip_file_obj.filename
        original_xlsx_filename = xlsx_file_obj.filename
        zip_name_part, zip_ext_part = os.path.splitext(original_zip_filename)
        xlsx_name_part, xlsx_ext_part = os.path.splitext(original_xlsx_filename)
        
        # 파일명이 없는 경우 UUID 기반으로, 있으면 secure_filename 처리
        secure_zip_name_part = secure_filename(zip_name_part) if zip_name_part else uuid.uuid4().hex
        secure_xlsx_name_part = secure_filename(xlsx_name_part) if xlsx_name_part else uuid.uuid4().hex
        zip_filename = secure_zip_name_part + zip_ext_part
        xlsx_filename = secure_xlsx_name_part + xlsx_ext_part

        zip_path = os.path.join(session_temp_dir, zip_filename)
        xlsx_path = os.path.join(session_temp_dir, xlsx_filename)
        
        zip_file_obj.save(zip_path)
        xlsx_file_obj.save(xlsx_path)
        app.logger.info(f"파일 저장 완료: {zip_path}, {xlsx_path}")

        extracted_images_path = os.path.join(session_temp_dir, "extracted_images")
        os.makedirs(extracted_images_path, exist_ok=True)
        app.logger.info(f"압축 해제 대상 폴더 준비: {extracted_images_path}")

        thread = threading.Thread(
            target=background_task,
            args=(subject_name, zip_path, xlsx_path, extracted_images_path, session_temp_dir, app.logger),
            name=f"BGTask-{os.path.basename(session_temp_dir)}" # 스레드 이름에 세션 ID 포함
        )
        thread.start()
        app.logger.info(f"백그라운드 스레드 시작됨 ({thread.name}) for session: {os.path.basename(session_temp_dir)}")

        return jsonify({"status": "processing_started", 
                        "message": "Files received and student ID recognition process started in background.",
                        "session_id": os.path.basename(session_temp_dir) # 임시 폴더명을 세션 ID로 활용하여 반환
                        }), 202

    except Exception as e:
        app.logger.error(f"recognize_student_id_endpoint 예외 발생: {traceback.format_exc()}")
        if session_temp_dir and os.path.exists(session_temp_dir): # 메인 스레드 오류 시 생성된 폴더 정리
            try:
                shutil.rmtree(session_temp_dir)
                app.logger.info(f"오류 발생으로 세션 폴더 ({session_temp_dir}) 삭제.")
            except Exception as e_rm:
                app.logger.warning(f"오류 발생 후 세션 폴더 ({session_temp_dir}) 삭제 실패: {e_rm}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

# 도식화 이미지에서 6, 7번 과정
# --- 2차 답안 인식 엔드포인트 (Kafka 기반 아키텍처와 호환성 재검토 필요) ---
@app.route('/recognize/answer', methods=['POST'])
def recognize_answer_endpoint():
    """2차 답안 인식 엔드포인트
    현재 로직은 로컬 파일 시스템에 의존하므로 Kafka 기반 아키텍처와 호환되지 않습니다.
    1차 처리 결과(Kafka 메시지)를 기반으로 이미지 데이터(예: base64)를 받고,
    정정된 학번 정보와 함께 답안 인식을 수행하도록 재설계가 필요합니다.
    """
    # 학번 정정 JSON 파일을 받고 학번 수정 과정 수행


    # 각 답안지 이미지에 대해 아래 작업을 수행한다.
        # 1. preprocess_answer_sheet
        # 2. recognize_answer_sheet_data

    
    
@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, World", 200

if __name__ == '__main__':
    # Spring과의 통신을 위해 0.0.0.0으로 호스트를 설정하고, 지정된 포트(예: 8080)를 사용합니다.
    # Docker 환경에서는 이 포트가 외부로 노출됩니다.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True는 개발 중에만 사용
