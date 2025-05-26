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

# Algorithm.OCR 모듈 import
from Algorithm.OCR.main_recognition import main_recognition_process
from Algorithm.OCR.main_recognition import DEFAULT_QN_DIRECTORY_PATH, DEFAULT_ANSWER_JSON_PATH, DEFAULT_OCR_RESULTS_JSON_PATH

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
            df = pd.read_excel(xlsx_path)
            # 학번이 있는 컬럼명을 알아야 함. 여기서는 '학번' 또는 첫 번째 컬럼으로 가정.
            if '학번' in df.columns:
                student_numbers_from_xlsx = df['학번'].astype(str).tolist()
            elif not df.empty:
                student_numbers_from_xlsx = df.iloc[:, 0].astype(str).tolist() # 첫번째 컬럼 사용
            else:
                student_numbers_from_xlsx = []
            app.logger.info(f"{len(student_numbers_from_xlsx)}개의 학번 로드 완료: {student_numbers_from_xlsx[:5]}...")
        except Exception as e:
            app.logger.error(f"XLSX 파싱 실패: {xlsx_path}, 오류: {e}")
            return jsonify({"error": f"Failed to parse xlsx file: {str(e)}"}), 500

        # 3. Student_id_recognition 모듈의 main 함수 호출
        # Student_id_recognition/main.py의 main 함수는 answer_sheet_dir_path를 인자로 받고,
        # 내부적으로 student_num_list를 사용함. 이 부분을 수정하거나, 함수 호출 방식을 맞춰야 함.
        # 여기서는 main.py의 make_json과 process_student_ids를 활용하여 로직을 구성
        
        # process_student_ids 함수가 직접 student_num_list를 받도록 수정하거나,
        # 전역 변수 등으로 공유하는 대신, 명시적으로 전달하는 것이 좋음.
        # 여기서는 main.py의 로직을 Flask에 맞게 조금 변형하여 직접 구성한다고 가정.
        
        # 먼저, Student_id_recognition/main.py의 make_json을 사용해 기본 구조 생성
        output_json = make_student_id_json(extracted_images_path) # 과목명 대신 디렉토리명 사용됨
        output_json["subject"] = subject_name # 요청받은 과목명으로 덮어쓰기
        output_json["student_list_from_xlsx_count"] = len(student_numbers_from_xlsx)

        # Student_id_recognition.main.process_student_ids를 직접 호출하는 대신,
        # 해당 함수의 핵심 로직을 여기에 통합하거나, process_student_ids가 student_numbers_from_xlsx를 받도록 수정 필요.
        # 현재 Student_id_recognition.main.main 함수는 student_num_list=[]로 시작하므로, XLSX 정보가 반영 안됨.
        # 임시로, process_student_ids를 호출하되, XLSX 학번 리스트를 어떻게든 전달해야 함.
        # 가장 간단한 방법은 process_student_ids 내부에서 XLSX를 읽도록 하거나, 전역변수 사용인데 좋지 않음.
        # 여기서는 Student_id_recognition.main.py의 로직을 직접 가져와서 XLSX 학번 리스트를 사용하도록 수정했다고 가정.
        # 또는, 해당 함수를 직접 호출하고, 그 결과를 후처리하는 방식을 취함.

        # 여기서는 process_student_ids를 호출하고, 반환된 결과에 xlsx 정보를 추가하는 방식으로 가정.
        # 이 방식은 process_student_ids 내부에서 student_num_list가 여전히 빈 리스트로 사용될 수 있음을 의미.
        # **중요**: Student_id_recognition/main.py의 main 함수가 XLSX 학번 리스트를 사용하도록 수정하는 것이 근본적인 해결책.
        
        # 현재 제공된 Student_id_recognition/main.py의 main 함수는 다음과 같이 동작:
        # 1. extracted_images_path (과목명 디렉토리)를 기준으로 JSON 기본 틀 생성
        # 2. extracted_images_path 내부의 각 이미지에 대해 extract_student_num 호출 (YOLO + PaddleOCR)
        # 3. 인식된 학번을 student_num_comparision에 전달 (이때 비교 대상 student_num_list는 함수 내에서 빈 리스트로 시작)
        # 4. 결과에 따라 파일명 변경 또는 JSON에 base64 데이터 추가
        
        # 이 흐름을 유지하되, student_num_comparision에 XLSX의 학번 리스트가 전달되어야 함.
        # 이를 위해 process_student_ids 함수 시그니처 변경 또는 내부 로직 수정이 필요.
        # 여기서는 함수 시그니처가 process_student_ids(answer_sheet_dir_path, xlsx_student_list)로 변경되었다고 가정하고 진행

        app.logger.info(f"학번 인식 모듈 호출 시작: {extracted_images_path}")
        try:
            # 수정된 process_student_ids 함수 호출
            result_from_module = process_student_ids(extracted_images_path, student_numbers_from_xlsx)
            
            # 과목명을 Flask에서 받은 것으로 통일
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
