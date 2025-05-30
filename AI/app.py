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
from student_id_recognition.main import main as process_student_ids
from student_id_recognition.main import make_json as make_student_id_json # make_json도 가져오기
from student_id_recognition.decompression_parsing.decompression import extract_archive
from student_id_recognition.decompression_parsing.parsing_xlsx import parsing_xlsx # parsing_xlsx 임포트 추가

# Algorithm.OCR 모듈 import
# from answer_recognition.main_recognition import main_recognition_process
# from answer_recognition.main_recognition import DEFAULT_QN_DIRECTORY_PATH, DEFAULT_ANSWER_JSON_PATH, DEFAULT_OCR_RESULTS_JSON_PATH

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
    try:
        # 1. 요청으로부터 데이터 가져오기 (새로운 변수명 사용)
        subject_name = request.form.get('subject')
        zip_file_obj = request.files.get('answerSheetZip')
        xlsx_file_obj = request.files.get('attendanceSheet')

        # Flask 로거 사용
        app.logger.info(f"Received subject: {subject_name}")
        if zip_file_obj:
            app.logger.info(f"Received answer sheet zip: {zip_file_obj.filename}")
        if xlsx_file_obj:
            app.logger.info(f"Received attendance sheet: {xlsx_file_obj.filename}")

        # 2. 필수 파라미터 검증
        if not subject_name:
            app.logger.error("Missing 'subject' in form data")
            return jsonify({"error": "Missing 'subject' in form data"}), 400
        if not zip_file_obj:
            app.logger.error("Missing 'answerSheetZip' in files")
            return jsonify({"error": "Missing 'answerSheetZip' in files"}), 400
        if not xlsx_file_obj:
            app.logger.error("Missing 'attendanceSheet' in files")
            return jsonify({"error": "Missing 'attendanceSheet' in files"}), 400

        # 파일명 유효성 검사
        if zip_file_obj.filename == '':
            app.logger.error("No selected zip file")
            return jsonify({"error": "No selected zip file"}), 400
        if xlsx_file_obj.filename == '':
            app.logger.error("No selected xlsx file")
            return jsonify({"error": "No selected xlsx file"}), 400
            
        # 파일 확장자 검사
        if not allowed_file(zip_file_obj.filename, ALLOWED_EXTENSIONS_ZIP):
            app.logger.error(f"Invalid zip_file type: {zip_file_obj.filename}")
            return jsonify({"error": "Invalid zip_file type"}), 400
        
        if not allowed_file(xlsx_file_obj.filename, ALLOWED_EXTENSIONS_XLSX):
            app.logger.error(f"Invalid xlsx_file type: {xlsx_file_obj.filename}")
            return jsonify({"error": "Invalid xlsx_file type"}), 400

        # 3. 각 요청별 고유한 임시 작업 폴더 생성
        session_temp_dir = tempfile.mkdtemp(dir=current_app.config['UPLOAD_FOLDER_BASE'])
        app.logger.info(f"세션 임시 폴더 생성: {session_temp_dir}")

        zip_filename = secure_filename(zip_file_obj.filename)
        xlsx_filename = secure_filename(xlsx_file_obj.filename)
        
        zip_path = os.path.join(session_temp_dir, zip_filename)
        xlsx_path = os.path.join(session_temp_dir, xlsx_filename)
        
        zip_file_obj.save(zip_path)
        xlsx_file_obj.save(xlsx_path)
        app.logger.info(f"파일 저장 완료: {zip_path}, {xlsx_path}")

        # 4. 압축 해제
        extracted_images_path = os.path.join(session_temp_dir, "extracted_images")
        os.makedirs(extracted_images_path, exist_ok=True)
        
        if not extract_archive(zip_path, extracted_images_path):
            app.logger.error(f"압축 해제 실패: {zip_path}")
            # shutil.rmtree(session_temp_dir) # 실패 시 임시폴더 정리 필요할 수 있음
            return jsonify({"error": "Failed to extract zip file"}), 500
        app.logger.info(f"압축 해제 완료: {zip_path} -> {extracted_images_path}")

        # 5. XLSX 파싱 (학번 리스트 생성)
        student_numbers_from_xlsx = []
        if os.path.exists(xlsx_path):
            try:
                student_numbers_from_xlsx = parsing_xlsx(xlsx_file_path=xlsx_path)
                if student_numbers_from_xlsx:
                    app.logger.info(f"{len(student_numbers_from_xlsx)}개의 학번 로드 완료: {student_numbers_from_xlsx[:5]}...")
                else:
                    app.logger.warning(f"XLSX 파일({xlsx_path})에서 학번 정보를 추출하지 못했습니다. 빈 리스트로 진행합니다.")
            except Exception as e:
                app.logger.error(f"XLSX 파싱 중 오류 발생: {xlsx_path}, 오류: {e}")
                # shutil.rmtree(session_temp_dir)
                return jsonify({"error": f"Failed to parse xlsx file: {str(e)}"}), 500
        else:
            # 이 경우는 위에서 파일 저장 실패 시 먼저 걸러지거나, save 이후 삭제된 극히 드문 케이스
            app.logger.error(f"XLSX 파일({xlsx_path})을 찾을 수 없습니다. 빈 리스트로 진행합니다.")
        
        # 6. Student_id_recognition 모듈의 main 함수 호출
        app.logger.info(f"학번 인식 모듈 호출 시작: Directory='{extracted_images_path}', Subject='{subject_name}'")
        try:
            result_from_module = process_student_ids(extracted_images_path, student_numbers_from_xlsx)
            
            # 과목명을 Flask에서 받은 것으로 통일 (모듈 내부에서도 subject를 설정하지만, 여기서 일관성 보장)
            result_from_module["subject"] = subject_name
            
            app.logger.info(f"학번 인식 모듈 처리 완료. 반환된 JSON 키: {list(result_from_module.keys())}")

        except Exception as e:
            app.logger.error(f"학번 인식 모듈 실행 중 오류: {traceback.format_exc()}")
            # shutil.rmtree(session_temp_dir)
            return jsonify({"error": f"Error during student ID recognition process: {str(e)}"}), 500
        
        return jsonify(result_from_module), 200

    except Exception as e:
        app.logger.error(f"1차 학번 인식 처리 중 예기치 않은 전체 오류: {traceback.format_exc()}")
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500
    finally:
        # finally 블록에서 session_temp_dir이 정의되었는지 확인 후 삭제
        if 'session_temp_dir' in locals() and os.path.exists(session_temp_dir):
            try:
                # shutil.rmtree(session_temp_dir) # 임시 폴더 자동 정리가 안될 경우 대비
                # app.logger.info(f"세션 임시 폴더 삭제 완료: {session_temp_dir}")
                pass # 현재는 자동 정리에 맡기거나, 필요시 주석 해제
            except Exception as e:
                app.logger.error(f"세션 임시 폴더 삭제 실패: {session_temp_dir}, 오류: {e}")
    # 정상적인 경우, 위에서 이미 jsonify(result_from_module), 200 등으로 반환됨.
    # 이 라인은 try 블록 내 모든 반환이 실패하고 finally까지 온 후 실행될 일은 거의 없음.
    # 만약의 경우를 대비한 기본 반환 (또는 로직 재검토 필요)
    # return jsonify({"status": "error", "message": "Reached end of function unexpectedly"}), 500

# @app.route('/recognize/answer', methods=['POST'])
# def recognize_answer_endpoint():
#     """2차 답안 인식 엔드포인트"""
#     try:
#         request_data = request.get_json()
#         if not request_data:
#             return jsonify({"error": "Invalid JSON payload"}), 400

#         subject_name = request_data.get('subject_name')
#         # answer_dir_path는 1차 처리(학번인식) 후 실제 이미지 파일들이 있는 경로여야 합니다.
#         # Spring이 이 경로를 정확히 알고 전달하거나, Flask가 생성한 경로를 사용해야 합니다.
#         answer_dir_path = request_data.get('answer_dir_path') # 예: /tmp/ocr_flask_uploads_xxxxxx/extracted_images
#         previous_step_json_data = request_data.get('previous_step_json_data') # 1차 학번인식 결과 JSON

#         if not subject_name or not answer_dir_path:
#             return jsonify({"error": "Missing subject_name or answer_dir_path in JSON payload"}), 400

#         # main_recognition_process에서 사용할 다른 경로들은 요청에서 받거나 기본값을 사용
#         qn_directory_path = request_data.get('qn_directory_path', DEFAULT_QN_DIRECTORY_PATH)
#         answer_json_path = request_data.get('answer_json_path', DEFAULT_ANSWER_JSON_PATH)
#         ocr_results_json_path = request_data.get('ocr_results_json_path', DEFAULT_OCR_RESULTS_JSON_PATH)
        
#         # output_json_base_path = os.path.join(current_app.config['UPLOAD_FOLDER_BASE'], subject_name + "_ocr_results")
#         # os.makedirs(output_json_base_path, exist_ok=True)
#         # ocr_results_json_path = os.path.join(output_json_base_path, "recognition_failures.json")
#         # 위처럼 동적으로 생성하거나, main_recognition_process의 기본 경로를 사용.

#         app.logger.info(f"2차 답안 인식 시작. Subject: {subject_name}, Answer Dir: {answer_dir_path}")

#         # main_recognition_process 호출
#         ocr_result = main_recognition_process(
#             subject_name=subject_name,
#             qn_directory_path=qn_directory_path,
#             answer_json_path=answer_json_path,
#             answer_dir_path=answer_dir_path, # 이 경로가 가장 중요
#             ocr_results_json_path=ocr_results_json_path,
#             previous_step_json_data=previous_step_json_data
#         )
#         app.logger.info(f"2차 답안 인식 처리 완료. Subject: {subject_name}")
#         return jsonify(ocr_result), 200

#     except Exception as e:
#         app.logger.error(f"2차 답안 인식 처리 중 오류: {traceback.format_exc()}")
#         return jsonify({"error": f"An unexpected error occurred during answer recognition: {str(e)}"}), 500
    
@app.route('/hello', methods=['GET'])
def hello():
    return "Hello, World", 200

if __name__ == '__main__':
    # Spring과의 통신을 위해 0.0.0.0으로 호스트를 설정하고, 지정된 포트(예: 8080)를 사용합니다.
    # Docker 환경에서는 이 포트가 외부로 노출됩니다.
    app.run(host='0.0.0.0', port=5000, debug=True) # debug=True는 개발 중에만 사용
