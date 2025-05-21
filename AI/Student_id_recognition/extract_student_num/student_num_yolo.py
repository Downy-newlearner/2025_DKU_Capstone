import subprocess
from pathlib import Path
import json
import os

def run_yolo_prediction(
    model_path: str = "/home/ysoh20/AI/Student_id_recognition/extract_student_num/best.pt",
    source_path: str = None,
    project: str = "results",
    name: str = "exp1",
    save_json: bool = True,
    save_txt: bool = True
) -> dict:
    """
    YOLO 모델을 사용하여 예측을 수행하는 함수

    Args:
        model_path (str): YOLO 모델 파일 경로
        source_path (str): 입력 이미지/디렉토리 경로
        project (str): 결과를 저장할 프로젝트 디렉토리
        name (str): 실험 이름
        save_json (bool): JSON 형식으로 결과 저장 여부
        save_txt (bool): 텍스트 형식으로 결과 저장 여부

    Returns:
        dict: 실행 결과 정보를 담은 딕셔너리
        {
            'success': bool,  # 실행 성공 여부
            'output': str,    # 실행 출력 메시지
            'error': str,     # 에러 메시지 (실패시)
            'results_dir': str # 결과 디렉토리 경로
        }
    """
    try:
        # 명령어 구성
        command = [
            "yolo",
            "predict",
            f"model={model_path}",
            f"source={source_path}",
            f"project={project}",
            f"name={name}",
            f"save_json={str(save_json).lower()}",
            f"save_txt={str(save_txt).lower()}"
        ]

        # 명령어 실행
        print(f"실행 명령어: {' '.join(command)}")
        result = subprocess.run(
            command,
            capture_output=True,
            text=True
        )

        # 결과 디렉토리 경로 생성
        results_dir = Path(project) / name

        # 실행 결과 반환
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'error': None,
                'results_dir': str(results_dir)
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': result.stderr,
                'results_dir': str(results_dir)
            }

    except Exception as e:
        return {
            'success': False,
            'output': None,
            'error': str(e),
            'results_dir': None
        }

if __name__ == "__main__":
    # 예제 사용
    result = run_yolo_prediction(
        source_path="/home/ysoh20/AI/Algorithm/OCR/test_answer",
        project="results",
        name="exp1"
    )

    if result['success']:
        print("YOLO 예측 성공!")
        print(f"결과 디렉토리: {result['results_dir']}")
    else:
        print("YOLO 예측 실패!")
        print(f"에러: {result['error']}") 