#!/bin/bash

# 결과를 저장할 JSON 파일 생성 및 시작 대괄호 추가
echo "[" > test_label.json

# labels 디렉토리의 모든 txt 파일을 처리
first_file=true
for file in results/exp1/labels/*.txt; do
    # 이미지 파일 이름 추출 (확장자 변경)
    image_name=$(basename "$file" .txt).jpg
    
    # JSON 객체 시작
    if [ "$first_file" = true ]; then
        first_file=false
    else
        echo "," >> test_label.json
    fi
    
    echo "{" >> test_label.json
    echo "  \"image\": \"$image_name\"," >> test_label.json
    echo "  \"detections\": [" >> test_label.json
    
    # txt 파일의 각 줄을 JSON 형식으로 변환
    first_line=true
    while IFS=" " read -r class_id x_center y_center width height confidence; do
        if [ "$first_line" = true ]; then
            first_line=false
        else
            echo "," >> test_label.json
        fi
        echo "    {" >> test_label.json
        echo "      \"class_id\": $class_id," >> test_label.json
        echo "      \"bbox\": [$x_center, $y_center, $width, $height]" >> test_label.json
        echo "    }" >> test_label.json
    done < "$file"
    
    echo "  ]" >> test_label.json
    echo "}" >> test_label.json
done

# JSON 파일 닫기
echo "]" >> test_label.json

echo "✅ JSON 파일 생성 완료: test_label.json"