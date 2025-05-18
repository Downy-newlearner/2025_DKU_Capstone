package com.checkmate.ai.controller;

import com.checkmate.ai.service.PdfService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

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

    @GetMapping("/{subject}/{studentId}")
    public ResponseEntity<ByteArrayResource> getPdfReport(@PathVariable String subject,
                                                          @PathVariable String studentId) {

        byte[] pdfBytes = pdfService.generatePdf(subject, studentId);

        ByteArrayResource resource = new ByteArrayResource(pdfBytes);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_PDF);
        headers.setContentDisposition(ContentDisposition.attachment()
                .filename(subject + "_" + studentId + "_report.pdf")
                .build());

        return new ResponseEntity<>(resource, headers, HttpStatus.OK);
    }

    // PDF 리포트 다운로드 (Flask 서버에서 가져옴)
    @GetMapping("/report/{subject}")
    public ResponseEntity<ByteArrayResource> downloadPdfReport(@PathVariable String subject) {
        return pdfService.downloadSubjectReportPdf(subject);
    }

}
