package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.mapper.ExamMapper;
import com.checkmate.ai.service.ExamService;
import com.checkmate.ai.service.LowConfidenceService;

import com.checkmate.ai.service.StudentService;
import lombok.extern.slf4j.Slf4j;
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

@Slf4j
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
    @Autowired
    private ExamService examService;


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
            // 파일명 변경
            studentService.renameFilesWithStudentId(dto);

            // ✅ subject로 exam 조회
            Exam exam = examService.findBySubject(dto.getSubject())
                    .orElseThrow(() -> new RuntimeException("해당 과목의 시험 정보를 찾을 수 없습니다."));

            // ✅ exam -> dto 변환
            ExamDto examDto = ExamMapper.toDto(exam);

            // ✅ Flask 전송을 위한 통합 DTO 구성
            StudentIdUpdateRequest request = new StudentIdUpdateRequest();
            request.setStudentIdUpdateDto(dto);
            request.setExamDto(examDto);

            // ✅ Flask로 전송
            String requestUrl = flaskServerUrl + "/recognize/answer";

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            HttpEntity<StudentIdUpdateRequest> requestEntity = new HttpEntity<>(request, headers);

            RestTemplate restTemplate = new RestTemplate();
            ResponseEntity<String> response = restTemplate.postForEntity(requestUrl, requestEntity, String.class);

            return ResponseEntity.ok("DTO 전송 완료: " + response.getBody());
        } catch (Exception e) {
            log.error("❌ DTO 전송 실패", e);
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("오류 발생: " + e.getMessage());
        }
    }

}












