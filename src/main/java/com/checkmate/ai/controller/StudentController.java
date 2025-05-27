package com.checkmate.ai.controller;

import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.dto.StudentIdUpdateDto;
import com.checkmate.ai.dto.StudentIdUpdateGetImageDto;
import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.service.LowConfidenceService;

import com.checkmate.ai.service.StudentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController
@RequestMapping("/student")
public class StudentController {


    @Value("${file.image-dir}")
    private String imageDirPath;


    @Value("${flask.server.url}")
    private String flaskServerUrl;


    @Autowired
    StudentService studentService;

    @Autowired
    private RestTemplate restTemplate;


    @Autowired
    private RedisTemplate<String, StudentIdUpdateGetImageDto> redisTemplate;




    @GetMapping("/{subject}/images")
    public ResponseEntity<?> getStudentImages(@PathVariable String subject) {
        String redisKey = "studentIdImages:" + subject;
        StudentIdUpdateGetImageDto dto = redisTemplate.opsForValue().get(redisKey);

        if (dto == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body("해당 과목에 대한 이미지 데이터가 없습니다.");
        }

        return ResponseEntity.ok(dto);
    }


    @PostMapping("/update-id")
    public ResponseEntity<?> appendAndSendToFlask(@RequestBody StudentIdUpdateDto dto) {
        try {
            studentService.renameFilesWithStudentId(dto); // 파일명 변경 로직 호출

            String requestUrl = flaskServerUrl+"/upload-image";
            String subject = dto.getSubject();

            for (StudentIdUpdateDto.student_list student : dto.getStudent_list()) {
                String studentId = student.getStudent_id();
                String fileName = student.getFile_name();
//                String base64 = student.getBase64_data();  // ✅ 단일 Base64

                Path studentDir = Paths.get(imageDirPath, subject);
                String newFileName = fileName + "_" + studentId + ".jpg";
                Path newFilePath = studentDir.resolve(newFileName);

                // Flask로 이미지 전송
                studentService.postImageToFlaskServer(newFilePath, requestUrl);
            }

            return ResponseEntity.ok("이미지 저장 및 Flask 전송 완료");
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("오류 발생");
        }
    }









}
