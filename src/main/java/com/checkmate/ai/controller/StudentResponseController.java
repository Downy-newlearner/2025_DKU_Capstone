package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.Student;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.service.ExamService;
import com.checkmate.ai.service.StudentResponseService;
import com.checkmate.ai.service.StudentService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/responses")
public class StudentResponseController {

    @Value("${flask.server.url}")
    private String flaskServerUrl;

    @Autowired
    private ExamService examService;

    @Autowired
    private StudentService studentService;

    @Autowired
    private StudentResponseService studentResponseService;

    @Autowired
    ObjectMapper objectMapper;

    @Autowired
    private RestTemplate restTemplate;



    @PostMapping("/upload-answer")
    public ResponseEntity<?> uploadAnswer(
            @RequestParam("subject") String subject,
            @RequestParam("answerSheetZip") MultipartFile answerSheetZip,
            @RequestParam("attendanceSheet") MultipartFile attendanceSheet
    ) {
        String requestUrl = flaskServerUrl+"/upload-answer";

        try {

            String answerZipExt = ".zip";
            String attendanceXlsxExt = ".xlsx";


            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();

            // subject는 일반 form-data 파라미터로 추가
            body.add("subject", subject);


            String answerOriginalName = answerSheetZip.getOriginalFilename();
            if (answerOriginalName != null && answerOriginalName.contains(".")) {
                answerZipExt = answerOriginalName.substring(answerOriginalName.lastIndexOf("."));
            }

            // answerSheetZip 파일 래핑 (파일명: subject + 확장자)
            String finalAnswerZipExt = answerZipExt;
            ByteArrayResource answerSheetResource = new ByteArrayResource(answerSheetZip.getBytes()) {
                @Override
                public String getFilename() {
                    return subject + finalAnswerZipExt;  // ex: math.zip
                }
            };
            body.add("answerSheetZip", answerSheetResource);

            // attendanceSheet 파일 확장자 추출 (ex: .csv)

            String attendanceOriginalName = attendanceSheet.getOriginalFilename();
            if (attendanceOriginalName != null && attendanceOriginalName.contains(".")) {
                attendanceXlsxExt = attendanceOriginalName.substring(attendanceOriginalName.lastIndexOf("."));
            }

            // attendanceSheet 파일 래핑 (파일명: subject + 확장자)
            String finalAttendanceExt = attendanceXlsxExt;
            ByteArrayResource attendanceSheetResource = new ByteArrayResource(attendanceSheet.getBytes()) {
                @Override
                public String getFilename() {
                    return subject + finalAttendanceExt;  // ex: math.csv
                }
            };
            body.add("attendanceSheet", attendanceSheetResource);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            // Flask 서버로 POST 전송
            ResponseEntity<String> response = restTemplate.postForEntity(requestUrl, requestEntity, String.class);

            return ResponseEntity.status(response.getStatusCode()).body(response.getBody());

        } catch (IOException e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("파일 전송 중 오류 발생");
        }
    }


    @GetMapping("/files/{fileName}")
    public ResponseEntity<Resource> downloadFile(@PathVariable String fileName) throws IOException {
        Path filePath = Paths.get("/your/path/to/files").resolve(fileName).normalize();

        Resource resource = new UrlResource(filePath.toUri());
        if (!resource.exists()) {
            throw new FileNotFoundException("File not found: " + fileName);
        }

        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + resource.getFilename() + "\"")
                .body(resource);
    }



    @GetMapping("/{subject}")
    public ResponseEntity<List<ZipListDto>> getStudentResponses(@PathVariable String subject) {
        List<ZipListDto> responses = studentResponseService.getStudentResponseZiplist(subject);

        if (responses.isEmpty()) {
            return ResponseEntity.noContent().build();
        }

        return ResponseEntity.ok(responses);
    }


    @PutMapping
    public ResponseEntity<String> updateStudentResponses(@RequestBody StudentAnswerUpdateDto dto) {
        studentResponseService.updateStudentResponses(dto);
        return ResponseEntity.ok("여러 학생의 답변이 성공적으로 업데이트되었습니다.");
    }

    @PostMapping("/simulate")
    public ResponseEntity<String> simulateKafkaMessage(@RequestBody KafkaStudentResponseDto dto) {
        try {
            // 1. 학생 정보 조회 또는 등록
            Student student = studentService.findById(dto.getStudent_id())
                    .orElseGet(() -> {
                        Student newStudent = new Student();
                        newStudent.setStudentId(dto.getStudent_id());
                        newStudent.setStudentName(dto.getStudent_name());
                        return studentService.save(newStudent);
                    });

            // 2. 과목에 대한 문제 목록 조회
            List<Question> questions = examService.getQuestionsBySubject(dto.getSubject());

            // 3. 채점 수행
            int totalScore = studentResponseService.safeGradeWithAnswerChecking(dto, questions, student);

            if (totalScore >= 0) {
                return ResponseEntity.ok("✅ 채점 완료 - 총점: " + totalScore);
            } else {
                return ResponseEntity.ok("⏳ 채점 지연 - 락 획득 실패");
            }

        } catch (Exception e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("❌ 처리 중 오류 발생: " + e.getMessage());
        }
    }



}

