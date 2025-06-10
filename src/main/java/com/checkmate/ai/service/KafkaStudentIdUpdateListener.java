package com.checkmate.ai.service;

import com.checkmate.ai.dto.StudentIdUpdateGetImageDto;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.Base64;
import java.util.List;


@Service
@Slf4j

public class KafkaStudentIdUpdateListener {


    @Value("${file.image-dir}")
    private String imageDirPath;


    @Autowired
    private RedisTemplate<String, StudentIdUpdateGetImageDto> redisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private StudentService studentService;


    @KafkaListener(topics = "student-id-image-requests", groupId = "image-fetch-group")
    public void listenStudentImageRequest(String message) {
        try {
            StudentIdUpdateGetImageDto requestDto = objectMapper.readValue(message, StudentIdUpdateGetImageDto.class);


            // Redis 저장
            String redisKey = "studentIdImages:" + requestDto.getSubject();
            redisTemplate.opsForValue().set(redisKey, requestDto);
            redisTemplate.expire(redisKey, Duration.ofMinutes(10));
            log.info("✅ Kafka 메시지 Redis 저장 완료 - key: {}", redisKey);

            // 이미지 디스크 저장
            String subject = requestDto.getSubject();
            Path saveDir = Paths.get(imageDirPath, subject, "studentId");
            Files.createDirectories(saveDir);

            List<StudentIdUpdateGetImageDto.LowConfidenceImages> images = requestDto.getLowConfidenceImages();
            for (StudentIdUpdateGetImageDto.LowConfidenceImages image : images) {
                String baseFileName = image.getFile_name();
                if (baseFileName == null || baseFileName.isEmpty()) {
                    baseFileName = "_";
                }

                String base64 = image.getBase64_data();
                if (base64 != null && !base64.isEmpty()) {
                    try {
                        String[] parts = base64.split(",");
                        byte[] imageBytes = Base64.getDecoder().decode(parts.length > 1 ? parts[1] : parts[0]);

                        String fileName = baseFileName;
                        Path filePath = saveDir.resolve(fileName);

                        Files.write(filePath, imageBytes);
                        log.info("✅ 이미지 저장 완료: {}", filePath);
                    } catch (Exception e) {
                        log.warn("❌ 이미지 저장 실패 - file: {}", baseFileName, e);
                    }
                }
            }

        } catch (Exception e) {
            log.error("❌ Kafka 메시지 처리 중 오류", e);
        }
    }





}
