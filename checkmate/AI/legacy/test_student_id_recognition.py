#!/usr/bin/env python3
"""
학번 인식 모듈 테스트 스크립트
"""
import sys
import os
import logging

# 경로 설정
sys.path.insert(0, os.path.dirname(__file__))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """테스트 메인 함수"""
    # 테스트 경로 설정
    extracted_path = '/Users/downy/Documents/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/legacy/신호및시스템-50/신호및시스템-50 2'
    xlsx_path = '/Users/downy/Documents/MLPA_auto_grading/2025_DKU_Capstone/checkmate/AI/legacy/신호및시스템-50/신호및시스템-50.xlsx'
    
    print('=' * 60)
    print('학번 인식 모듈 테스트')
    print('=' * 60)
    print(f'이미지 폴더: {extracted_path}')
    print(f'XLSX 파일: {xlsx_path}')
    print()
    
    # 1. XLSX 파싱 (선택적)
    student_numbers = []
    try:
        from student_id_recognition.decompression_parsing.parsing_xlsx import parsing_xlsx
        print('1. XLSX 파싱 중...')
        student_numbers = parsing_xlsx(xlsx_path, logger)
        print(f'   ✓ 학번 {len(student_numbers)}개 추출')
        if student_numbers:
            print(f'   예시: {student_numbers[:5]}')
    except Exception as e:
        print(f'   ⚠ XLSX 파싱 실패 (계속 진행): {e}')
        student_numbers = []
    
    print()
    
    # 2. 학번 인식
    try:
        from student_id_recognition.main import main as recognize_student_ids
        
        print('2. 학번 인식 시작...')
        print('   (YOLO 모델 로드 및 OCR 초기화 중...)')
        
        result = recognize_student_ids(
            extracted_images_path=extracted_path,
            student_numbers_from_xlsx=student_numbers,
            subject_name='신호및시스템-50',
            producer=None,  # Kafka 없이 테스트
            student_id_recognition_topic='test-topic',
            task_identifier='test-task'
        )
        
        print()
        print('=' * 60)
        print('결과')
        print('=' * 60)
        print(f'과목: {result["subject"]}')
        print(f'낮은 신뢰도 이미지 수: {len(result["lowConfidenceImages"])}')
        
        if result['lowConfidenceImages']:
            print('\n낮은 신뢰도 이미지 목록:')
            for i, img in enumerate(result['lowConfidenceImages'], 1):
                print(f'  {i}. {img["file_name"]}')
                if 'error' in img:
                    print(f'     오류: {img["error"]}')
        else:
            print('\n✓ 모든 이미지가 높은 신뢰도로 인식되었습니다!')
        
        # 디버그 JSON 파일 확인
        debug_json_path = os.path.join(extracted_path, "student_id_recognition_debug.json")
        if os.path.exists(debug_json_path):
            print(f'\n디버그 JSON 파일 생성됨: {debug_json_path}')
        
        print()
        print('=' * 60)
        print('테스트 완료')
        print('=' * 60)
        
    except ImportError as e:
        print(f'\n✗ 모듈 import 실패: {e}')
        print('\n필요한 패키지를 설치해주세요:')
        print('  pip install pillow ultralytics paddleocr opencv-python numpy')
        sys.exit(1)
    except Exception as e:
        print(f'\n✗ 오류 발생: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

