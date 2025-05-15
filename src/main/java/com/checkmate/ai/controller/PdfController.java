package com.checkmate.ai.controller;

import com.checkmate.ai.service.PdfService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/report")
public class PdfController {

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
}
