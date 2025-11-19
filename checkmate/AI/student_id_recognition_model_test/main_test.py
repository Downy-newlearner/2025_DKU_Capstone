#!/usr/bin/env python3
"""
전체 테스트 파이프라인 실행
1. test_models.py - YOLO 모델 테스트 및 시각화
2. crop_yolo_result.py - YOLO 결과 크롭
3. paddle_test.py - PaddleOCR 인식
"""
import subprocess
import sys
import os
import re

# 스크립트 디렉토리
SCRIPT_DIR = os.path.dirname(__file__)
EXP_BASE_DIR = os.path.join(SCRIPT_DIR, "exp")


def get_ordinal_suffix(n):
    """숫자를 ordinal 형식으로 변환 (1st, 2nd, 3rd, 4th...)"""
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def get_next_experiment_number():
    """다음 실험 번호 결정"""
    if not os.path.exists(EXP_BASE_DIR):
        return 1
    
    # exp 디렉토리 내의 모든 디렉토리 확인
    existing_dirs = [
        d for d in os.listdir(EXP_BASE_DIR)
        if os.path.isdir(os.path.join(EXP_BASE_DIR, d))
    ]
    
    if not existing_dirs:
        return 1
    
    # 숫자 추출 (예: "1st" -> 1, "2nd" -> 2)
    numbers = []
    for dir_name in existing_dirs:
        match = re.match(r'(\d+)(st|nd|rd|th)', dir_name)
        if match:
            numbers.append(int(match.group(1)))
    
    if not numbers:
        return 1
    
    return max(numbers) + 1


def run_script(script_name, exp_number):
    """스크립트 실행"""
    script_path = os.path.join(SCRIPT_DIR, script_name)
    print(f"\n{'='*60}")
    print(f"{script_name} 실행 중...")
    print(f"{'='*60}\n")
    
    env = os.environ.copy()
    env['EXPERIMENT_NUMBER'] = str(exp_number)
    
    result = subprocess.run(
        [sys.executable, script_path],
        cwd=SCRIPT_DIR,
        env=env,
        capture_output=False
    )
    
    if result.returncode != 0:
        print(f"\n❌ {script_name} 실행 실패 (종료 코드: {result.returncode})")
        return False
    
    print(f"\n✓ {script_name} 완료")
    return True


def main():
    print("="*60)
    print("전체 테스트 파이프라인 시작")
    print("="*60)
    
    # 실험 번호 결정
    exp_number = get_next_experiment_number()
    exp_name = get_ordinal_suffix(exp_number)
    exp_dir = os.path.join(EXP_BASE_DIR, exp_name)
    
    print(f"\n실험 번호: {exp_name}")
    print(f"실험 디렉토리: {exp_dir}")
    
    scripts = [
        "test_models.py",
        "crop_yolo_result.py",
        "paddle_test.py"
    ]
    
    for script in scripts:
        if not run_script(script, exp_number):
            print(f"\n❌ 파이프라인 중단: {script} 실패")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("전체 파이프라인 완료!")
    print(f"결과 저장 위치: {exp_dir}")
    print("="*60)


if __name__ == '__main__':
    main()

