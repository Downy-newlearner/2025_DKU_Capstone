import sys # 경로 추가를 위해 import
from flask import Flask, request, jsonify, current_app
import os
import tempfile
import traceback
import zipfile # decompression 모듈 내부에서 사용하지만, 여기서도 파일 타입 체크 등에 사용 가능
import pandas as pd # XLSX 처리용
from werkzeug.utils import secure_filename # 안전한 파일명 생성

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
from Student_id_recognition.main import main as process_student_ids
from Student_id_recognition.main import make_json as make_student_id_json # make_json도 가져오기
from Student_id_recognition.decompression_parsing.decompression import extract_archive
from Student_id_recognition.decompression_parsing.parsing_xlsx import parsing_xlsx # parsing_xlsx 임포트 추가

# Algorithm.OCR 모듈 import
from Answer_recognition.main_recognition import main_recognition_process
from Answer_recognition.main_recognition import DEFAULT_QN_DIRECTORY_PATH, DEFAULT_ANSWER_JSON_PATH, DEFAULT_OCR_RESULTS_JSON_PATH

app = Flask(__name__)

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

@app.route('/recognize/student_id', methods=['POST'])
def recognize_student_id_endpoint():
    """1차 학번 인식 엔드포인트"""
    if 'zip_file' not in request.files or 'xlsx_file' not in request.files:
        return jsonify({"error": "Missing zip_file or xlsx_file in the request"}), 400
    
    zip_file = request.files['zip_file']
    xlsx_file = request.files['xlsx_file']
    subject_name = request.form.get('subject', 'DefaultSubject') # 과목명 (선택적)

    if zip_file.filename == '' or xlsx_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not (zip_file and allowed_file(zip_file.filename, ALLOWED_EXTENSIONS_ZIP)):
        return jsonify({"error": "Invalid zip_file type"}), 400
    
    if not (xlsx_file and allowed_file(xlsx_file.filename, ALLOWED_EXTENSIONS_XLSX)):
        return jsonify({"error": "Invalid xlsx_file type"}), 400

    # 각 요청별 고유한 임시 작업 폴더 생성
    try:
        session_temp_dir = tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER_BASE'])
        app.logger.info(f"세션 임시 폴더 생성: {session_temp_dir}")

        zip_filename = secure_filename(zip_file.filename)
        xlsx_filename = secure_filename(xlsx_file.filename)
        
        zip_path = os.path.join(session_temp_dir, zip_filename)
        xlsx_path = os.path.join(session_temp_dir, xlsx_filename)
        
        zip_file.save(zip_path)
        xlsx_file.save(xlsx_path)
        app.logger.info(f"파일 저장 완료: {zip_path}, {xlsx_path}")

        # 1. 압축 해제
        # extract_archive는 압축 파일명 기준으로 하위 폴더를 생성하므로, 그 경로를 잘 관리해야 함.
        # 압축 해제될 경로를 명시적으로 지정 (예: session_temp_dir/extracted_images)
        extracted_images_path = os.path.join(session_temp_dir, "extracted_images")
        os.makedirs(extracted_images_path, exist_ok=True)
        
        if not extract_archive(zip_path, extracted_images_path):
            app.logger.error(f"압축 해제 실패: {zip_path}")
            return jsonify({"error": "Failed to extract zip file"}), 500
        app.logger.info(f"압축 해제 완료: {zip_path} -> {extracted_images_path}")

        # 2. XLSX 파싱 (학번 리스트 생성)
        try:
            # student_numbers_from_xlsx = parsing_xlsx(xlsx_file_path=xlsx_path) # parsing_xlsx 함수 사용
            # 위 라인 대신, 파일 존재 유무 확인 및 예외 처리 포함하여 main.py 스타일로 변경
            if os.path.exists(xlsx_path):
                student_numbers_from_xlsx = parsing_xlsx(xlsx_file_path=xlsx_path)
                if student_numbers_from_xlsx:
                    app.logger.info(f"{len(student_numbers_from_xlsx)}개의 학번 로드 완료 (parsing_xlsx 사용): {student_numbers_from_xlsx[:5]}...")
                else:
                    app.logger.warning(f"XLSX 파일({xlsx_path})에서 학번 정보를 추출하지 못했습니다 (parsing_xlsx 사용). 빈 리스트로 진행합니다.")
                    student_numbers_from_xlsx = []
            else:
                app.logger.error(f"XLSX 파일({xlsx_path})을 찾을 수 없습니다. 빈 리스트로 진행합니다.")
                student_numbers_from_xlsx = []

        except Exception as e:
            app.logger.error(f"XLSX 파싱 중 오류 발생 (parsing_xlsx 사용): {xlsx_path}, 오류: {e}")
            return jsonify({"error": f"Failed to parse xlsx file using parsing_xlsx: {str(e)}"}), 500
        
        # 3. Student_id_recognition 모듈의 main 함수 호출 (process_student_ids로 alias됨)
        # Student_id_recognition/main.py의 main 함수 시그니처는 (answer_sheet_dir_path, student_id_list) 입니다.
        # extracted_images_path는 압축 해제된 이미지들이 있는 디렉토리 경로입니다.
        # student_numbers_from_xlsx는 파싱된 학번 리스트입니다.

        app.logger.info(f"학번 인식 모듈 호출 시작: {extracted_images_path}")
        try:
            # Student_id_recognition/main.py의 main 함수 (여기서는 process_student_ids) 호출
            result_from_module = process_student_ids(extracted_images_path, student_numbers_from_xlsx)
            
            # 과목명을 Flask에서 받은 것으로 통일 (이미 JSON 구조 내에 subject가 있지만, 여기서 한번 더 보장)
            result_from_module["subject"] = subject_name
            
            app.logger.info(f"학번 인식 모듈 처리 완료.")

        except Exception as e:
            app.logger.error(f"학번 인식 모듈 실행 중 오류: {traceback.format_exc()}")
            return jsonify({"error": f"Error during student ID recognition process: {str(e)}"}), 500
        
        return jsonify(result_from_module), 200

    except Exception as e:
        app.logger.error(f"1차 학번 인식 처리 중 전체 오류: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        # 세션 임시 폴더 및 내용 삭제 (선택적)
        # if 'session_temp_dir' in locals() and os.path.exists(session_temp_dir):
        #     try:
        #         shutil.rmtree(session_temp_dir)
        #         app.logger.info(f"세션 임시 폴더 삭제 완료: {session_temp_dir}")
        #     except Exception as e:
        #         app.logger.error(f"세션 임시 폴더 삭제 실패: {session_temp_dir}, 오류: {e}")
        pass # tempfile.mkdtemp로 생성된 폴더는 프로그램 종료 시 OS에 의해 정리될 수 있으나, 명시적 관리가 더 안전

@app.route('/recognize/answer', methods=['POST'])
def recognize_answer_endpoint():
    """2차 답안 인식 엔드포인트"""
    try:
        request_data = request.get_json()
        if not request_data:
            return jsonify({"error": "Invalid JSON payload"}), 400

        subject_name = request_data.get('subject_name')
        # answer_dir_path는 1차 처리(학번인식) 후 실제 이미지 파일들이 있는 경로여야 합니다.
        # Spring이 이 경로를 정확히 알고 전달하거나, Flask가 생성한 경로를 사용해야 합니다.
        answer_dir_path = request_data.get('answer_dir_path') # 예: /tmp/ocr_flask_uploads_xxxxxx/extracted_images
        previous_step_json_data = request_data.get('previous_step_json_data') # 1차 학번인식 결과 JSON

        if not subject_name or not answer_dir_path:
            return jsonify({"error": "Missing subject_name or answer_dir_path in JSON payload"}), 400

        # main_recognition_process에서 사용할 다른 경로들은 요청에서 받거나 기본값을 사용
        qn_directory_path = request_data.get('qn_directory_path', DEFAULT_QN_DIRECTORY_PATH)
        answer_json_path = request_data.get('answer_json_path', DEFAULT_ANSWER_JSON_PATH)
        ocr_results_json_path = request_data.get('ocr_results_json_path', DEFAULT_OCR_RESULTS_JSON_PATH)
        
        # output_json_base_path = os.path.join(current_app.config['UPLOAD_FOLDER_BASE'], subject_name + "_ocr_results")
        # os.makedirs(output_json_base_path, exist_ok=True)
        # ocr_results_json_path = os.path.join(output_json_base_path, "recognition_failures.json")
        # 위처럼 동적으로 생성하거나, main_recognition_process의 기본 경로를 사용.

        app.logger.info(f"2차 답안 인식 시작. Subject: {subject_name}, Answer Dir: {answer_dir_path}")

        # main_recognition_process 호출
        ocr_result = main_recognition_process(
            subject_name=subject_name,
            qn_directory_path=qn_directory_path,
            answer_json_path=answer_json_path,
            answer_dir_path=answer_dir_path, # 이 경로가 가장 중요
            ocr_results_json_path=ocr_results_json_path,
            previous_step_json_data=previous_step_json_data
        )
        app.logger.info(f"2차 답안 인식 처리 완료. Subject: {subject_name}")
        return jsonify(ocr_result), 200

    except Exception as e:
        app.logger.error(f"2차 답안 인식 처리 중 오류: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred during answer recognition: {str(e)}"}), 500

if __name__ == '__main__':
    # Spring과의 통신을 위해 0.0.0.0으로 호스트를 설정하고, 지정된 포트(예: 8080)를 사용합니다.
    # Docker 환경에서는 이 포트가 외부로 노출됩니다.
    app.run(host='0.0.0.0', port=8080, debug=True) # debug=True는 개발 중에만 사용
