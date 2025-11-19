'''
rename_answer_files.py
답안 이미지 파일들의 이름을 문제 번호와 정답 개수 정보를 포함하도록 변경하는 모듈

Param: y좌표 딕셔너리, 답지, ans 디렉토리 path
-> ans 파일명 변경
Return: x
'''

import os
import json
from typing import Dict, List, Union

def rename_answer_files(
    question_info_dict: Dict[str, List[int]],
    answer_json_path: str,
    answer_dir_path: str
):
    """
    답안 이미지 파일들의 이름을 문제 번호와 정답 개수 정보를 포함하도록 변경
    
    Args:
        question_info_dict: y좌표 정보가 있는 딕셔너리
        answer_json_path: 답지 파일 경로
        answer_dir_path: ans 디렉토리 경로
    """
    # Load answer count information from JSON file
    with open(answer_json_path, 'r', encoding='utf-8') as f:
        answer_counts = json.load(f)
    
    # Get all answer folders
    answer_folders = [f for f in os.listdir(answer_dir_path) if os.path.isdir(os.path.join(answer_dir_path, f))]
    
    for folder in answer_folders:
        # Extract y_top and y_bottom from folder name
        # Format: answer_number_ytop_ybottom
        parts = folder.split('_')
        if len(parts) >= 4:
            try:
                # Remove any file extension from the last part
                last_part = parts[3].split('.')[0]
                y_top = int(parts[2])
                y_bottom = int(last_part)
                y_center = (y_top + y_bottom) // 2
                
                # Find corresponding question number
                matching_qn = None
                for qn, y_coords in question_info_dict.items():
                    if y_coords[0] <= y_center <= y_coords[1]:  # y_coords[0]은 y_top, y_coords[1]은 y_bottom
                        matching_qn = qn
                        break
                
                if matching_qn:
                    folder_path = os.path.join(answer_dir_path, folder)
                    # Process all image files in the folder
                    for file in os.listdir(folder_path):
                        if file.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
                            # Get answer count for the question
                            # Find the question in the questions array
                            question_data = next(
                                (q for q in answer_counts['questions'] 
                                if q['question_number'] == matching_qn),
                                None
                            )
                            answer_count = question_data['answer_counts'] if question_data else 0
                            
                            # Get original extension
                            file_ext = os.path.splitext(file)[1].lower()
                            base_name = os.path.splitext(file)[0]
                            
                            # If file already has qn and ac, remove them
                            if '_qn_' in base_name and '_ac_' in base_name:
                                # Remove existing qn and ac values
                                parts = base_name.split('_qn_')
                                base_name = parts[0]
                            
                            # Create new filename
                            new_filename = f"{base_name}_qn_{matching_qn}_ac_{answer_count}{file_ext}"
                            
                            # Rename the file
                            old_path = os.path.join(folder_path, file)
                            new_path = os.path.join(folder_path, new_filename)
                            os.rename(old_path, new_path)
                            print(f"Renamed: {file} -> {new_filename}")
            except (ValueError, IndexError) as e:
                print(f"Warning: Could not process folder {folder}: {str(e)}")
                continue

if __name__ == "__main__":
    # For standalone testing
    base_dir = '/home/ysoh20/AI'
    
    # Paths
    answer_json_path = "answer_counts.json"
    answer_dir_path = os.path.join(base_dir, 'Algorithm/OCR/cropped_datasets/text_crop_new/answer')
    
    # Process files
    # question_info_dict는 외부에서 받아와야 함
    # rename_answer_files(question_info_dict, answer_json_path, answer_dir_path) 