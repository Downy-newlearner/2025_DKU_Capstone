FROM openjdk:17-jdk-slim

# 작업 디렉토리 설정
WORKDIR /app

# JAR 파일 복사
COPY build/libs/*.jar app.jar

# 이미지 파일 복사
COPY docker-images/ /app/static/images/

# 포트 노출
EXPOSE 8080

ENV IMAGE_DIR=/app/static/images

# 실행
ENTRYPOINT ["java", "-jar", "app.jar"]
