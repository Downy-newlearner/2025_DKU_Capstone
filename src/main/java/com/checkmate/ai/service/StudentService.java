package com.checkmate.ai.service;

import com.checkmate.ai.dto.StudentIdUpdateDto;
import com.checkmate.ai.dto.StudentIdUpdateDto.student_list;
import com.checkmate.ai.dto.StudentIdUpdateGetImageDto;
import com.checkmate.ai.entity.Student;
import com.checkmate.ai.repository.jpa.StudentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;


@Slf4j
@Service
public class StudentService {

    @Value("${file.image-dir}")
    private String imageDirPath;

    @Autowired
    private StudentRepository studentRepository;



    public Optional<Student> findById(String id) {
        return studentRepository.findById(id);
    }
    public Student save(Student student) {
        return studentRepository.save(student);
    }


    public void renameFilesWithStudentId(StudentIdUpdateDto dto) {
        String subject = dto.getSubject();
        Path studentDir = Paths.get(imageDirPath, subject);

        for (StudentIdUpdateDto.student_list student : dto.getStudent_list()) {
            String studentId = student.getStudent_id();
            String originalFileName = student.getFile_name();

            String baseFileName = (originalFileName == null || originalFileName.isEmpty()) ? "_" : originalFileName;

            String oldFileName = baseFileName + ".jpg";
            Path oldFilePath = studentDir.resolve(oldFileName);

            String newFileName = baseFileName + "_" + studentId + ".jpg";
            Path newFilePath = studentDir.resolve(newFileName);

            try {
                if (Files.exists(oldFilePath)) {
                    Files.move(oldFilePath, newFilePath, StandardCopyOption.REPLACE_EXISTING);
                    log.info("✅ 파일명 변경: {} -> {}", oldFileName, newFileName);
                } else {
                    log.warn("⚠️ 파일이 존재하지 않음: {}", oldFileName);
                }
            } catch (IOException e) {
                log.error("❌ 파일명 변경 실패", e);
            }
        }
    }



    public void postImageToFlaskServer(Path imagePath, String flaskUrl) {
        try {
            byte[] imageBytes = Files.readAllBytes(imagePath);
            String base64Image = Base64.getEncoder().encodeToString(imageBytes);

            // JSON body 생성
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("fileName", imagePath.getFileName().toString());
            requestBody.put("imageData", base64Image);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);

            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<String> response = restTemplate.postForEntity(flaskUrl, request, String.class);

            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("✅ Flask 서버로 이미지 전송 성공: {}", imagePath.getFileName());
            } else {
                log.warn("⚠️ Flask 서버 응답 실패: {}", response.getStatusCode());
            }

        } catch (IOException e) {
            log.error("❌ 이미지 파일 읽기 실패", e);
        } catch (Exception e) {
            log.error("❌ Flask 서버 전송 실패", e);
        }
    }






}
