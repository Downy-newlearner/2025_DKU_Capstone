package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.Student;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.service.ExamService;
import com.checkmate.ai.service.PdfService;
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
import org.springframework.web.util.UriUtils;

import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@RestController

public class StudentResponseController {

    @Value("${flask.server.url}")
    private String flaskServerUrl;

    @Autowired
    private ExamService examService;

    @Autowired
    private StudentService studentService;

    @Autowired
    private PdfService pdfService;

    @Autowired
    private StudentResponseService studentResponseService;

    @Autowired
    ObjectMapper objectMapper;

    @Autowired
    private RestTemplate restTemplate;



    @PostMapping("/responses/upload-answer")
    public ResponseEntity<?> uploadAnswer(
            @RequestParam("subject") String subject,
            @RequestParam("answerSheetZip") MultipartFile answerSheetZip,
            @RequestParam("attendanceSheet") MultipartFile attendanceSheet
    ) {
        String requestUrl = flaskServerUrl+"/recognize/student_id";

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
                    return subject+ finalAnswerZipExt;  // ex: math.zip
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


    @GetMapping("/file/{fileName:.+}")
    public ResponseEntity<byte[]> downloadZipFile(@PathVariable String fileName) throws IOException {
        // 1. fileName 파싱
        String encodedFileName = UriUtils.encode(fileName, StandardCharsets.UTF_8);
        System.out.println(fileName);
        if (!fileName.endsWith(".zip") || !fileName.contains("_")) {
            throw new IllegalArgumentException("파일 이름 형식이 올바르지 않습니다. (예: subject_studentId.zip)");
        }

        String[] parts = fileName.replace(".zip", "").split("_");
        if (parts.length != 2) {
            throw new IllegalArgumentException("파일 이름에서 과목과 학번을 파싱할 수 없습니다.");
        }

        String subject = parts[0];
        String studentId = parts[1];

        Student student = studentService.getStudentById(studentId);


        List<byte[]> imagesBytes = pdfService.fetchImagesFromFlask(studentId, subject);
        byte[] pdfBytes = pdfService.generatePdf(subject, student);


        byte[] zipBytes = pdfService.createZipWithPdfAndImages(subject, student, pdfBytes,imagesBytes);


// ✅ 2. 서버 루트 디렉토리 하위에 ZIP 저장
        Path projectRoot = Paths.get(System.getProperty("user.dir")); // 현재 실행 중인 프로젝트의 루트 디렉토리
        Path saveDir = projectRoot.resolve("zips"); // 루트/zips 경로

        if (!Files.exists(saveDir)) {
            Files.createDirectories(saveDir);
        }

        Path zipPath = saveDir.resolve(fileName); // 루트/zips/fileName.zip
        Files.write(zipPath, zipBytes); // ZIP 파일 저장


        // 4. 클라이언트로 응답
        return ResponseEntity.ok()
                .contentType(MediaType.APPLICATION_OCTET_STREAM)
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename*=UTF-8''" + encodedFileName)
                .body(zipBytes);
    }




    @GetMapping("/responses/{subject}")
    public ResponseEntity<List<ZipListDto>> getStudentResponses(@PathVariable String subject) {

        List<ZipListDto> responses = studentResponseService.getStudentResponseZiplist(subject);

        if (responses.isEmpty()) {
            return ResponseEntity.noContent().build();
        }

        return ResponseEntity.ok(responses);
    }


    @PutMapping("/responses")
    public ResponseEntity<Map<String, String>> updateStudentResponses(@RequestBody StudentAnswerUpdateDto dto) {
        studentResponseService.updateStudentResponses(dto);
        return ResponseEntity.ok(Map.of(
                "status", "DONE"
        ));

    }





}

