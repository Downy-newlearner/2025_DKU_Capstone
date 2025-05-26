# Base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies if any (e.g., for opencv or other C-based libraries)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     libgl1-mesa-glx libglib2.0-0 \
#  && apt-get clean \
#  && rm -rf /var/lib/apt/lists/*
# 위 부분은 paddleocr, opencv 등의 실행에 필요할 수 있으므로, 실행 시 오류가 발생하면 주석 해제 및 필요한 패키지 추가

# Install python dependencies
# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# AI 폴더와 app.py 등을 복사합니다.
# .dockerignore 파일을 사용하여 불필요한 파일(예: .git, __pycache__, 로컬 테스트 데이터) 복사를 방지할 수 있습니다.
COPY . /app

# Expose port (Flask app runs on 8080)
EXPOSE 8080

# Command to run the application
CMD ["python", "app.py"]