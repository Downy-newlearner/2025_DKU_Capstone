package com.checkmate.ai.controller;

import com.checkmate.ai.entity.Student;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.repository.jpa.ExamRepository;
import com.checkmate.ai.service.PdfService;
import com.checkmate.ai.service.StudentResponseService;
import com.checkmate.ai.service.StudentService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/report")
public class PdfController {

    @Value("${file.image-dir}")
    private String imageDir;

    @Value("${flask.server.url}")
    private String flaskReportUrl;

    @Autowired
    private RestTemplate restTemplate;
    @Autowired
    private PdfService pdfService;
    @Autowired
    private StudentService studentService;
    @Autowired
    private StudentResponseService studentResponseService;



//    @GetMapping("/files/{fileName:.+}")
//    public ResponseEntity<Resource> serveZipFile(@PathVariable String fileName) throws IOException {
//        // 경로 설정 (예: 로컬 디렉터리 또는 S3 등)
//        Path zipFilePath = Paths.get("/your/zip/storage/path").resolve(fileName);
//
//        if (!Files.exists(zipFilePath)) {
//            return ResponseEntity.notFound().build();
//        }
//
//        Resource resource = new UrlResource(zipFilePath.toUri());
//
//        return ResponseEntity.ok()
//                .contentType(MediaType.APPLICATION_OCTET_STREAM)
//                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"" + fileName + "\"")
//                .body(resource);
//    }
//





    @GetMapping("/{subject}/{studentId}")
    public ResponseEntity<ByteArrayResource> getPdfReport(@PathVariable String subject,
                                                          @PathVariable String studentId) {

        Optional<Student> studentOpt = studentService.findById(studentId);

        if (studentOpt.isEmpty()) {
            return ResponseEntity.notFound().build(); // 학생이 없으면 404 반환
        }

        Student student = studentOpt.get();

        byte[] pdfBytes = pdfService.generatePdf(subject, student);

        ByteArrayResource resource = new ByteArrayResource(pdfBytes);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(ContentDisposition.attachment()
                .filename(subject + "_" + studentId + "_report.pdf")
                .build());

        return new ResponseEntity<>(resource, headers, HttpStatus.OK);
    }


    // PDF 리포트 다운로드 (Flask 서버에서 가져옴)
    @PostMapping("/{subject}")
    public ResponseEntity<ByteArrayResource> downloadPdfReport(@PathVariable String subject) {

        List<StudentResponse> responses = studentResponseService.getStudentResponses(subject);


        return pdfService.downloadSubjectReportPdf(subject, responses);
    }

}
