FROM openjdk:17-jdk-slim

# 작업 디렉토리 설정
WORKDIR /app

# JAR 파일 복사
COPY build/libs/*.jar app.jar

# 이미지 파일 복사
COPY docker-images/ /app/static/images/

# 폰트 파일 복사 (한글 지원용)
COPY src/main/resources/static/fonts/NanumGothic.ttf /app/static/fonts/NanumGothic.ttf

# 포트 노출
EXPOSE 8080

# 환경 변수 (이미지 경로 등)
ENV IMAGE_DIR=/app/static/images \
    FONT_PATH=/app/static/fonts/NanumGothic.ttf

# 실행
ENTRYPOINT ["java", "-jar", "app.jar"]
