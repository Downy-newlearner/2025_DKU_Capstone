package com.checkmate.ai.controller;

import com.checkmate.ai.dto.Base64ImageDto;
import com.checkmate.ai.service.FileService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestOperations;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
public class FileController {

    @Value("${flask.server.url}")
    private String flaskServerUrl;

    @Autowired
    private FileService fileService;

    @Autowired
    private RestTemplate restTemplate;

    @GetMapping("images/{subject}/low-confidence-images")
    public List<Base64ImageDto> getBase64Images(@PathVariable("subject") String subject) {
        return fileService.getLowConfidenceImages(subject);
    }

    // ZIP 파일 받아서 Flask 서버로 전송
    @PostMapping("/upload-zip")
    public ResponseEntity<String> uploadZipAndForwardToFlask(@RequestParam("file") MultipartFile zipFile) {
        System.out.println(flaskServerUrl);
        if (zipFile.isEmpty()) {
            return ResponseEntity.badRequest().body("업로드된 파일이 없습니다.");
        }

        try {
            // Flask 서버에 보낼 MultiPart 요청 생성
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            // MultipartFile -> ByteArrayResource 래핑 필요
            ByteArrayResource byteArrayResource = new ByteArrayResource(zipFile.getBytes()) {
                @Override
                public String getFilename() {
                    return zipFile.getOriginalFilename();
                }
            };
            body.add("file", byteArrayResource);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            HttpEntity<MultiValueMap<String, Object>> requestEntity = new HttpEntity<>(body, headers);

            // Flask 서버에 POST 요청 보내기
            ResponseEntity<String> response = restTemplate.postForEntity(flaskServerUrl, requestEntity, String.class);

            // Flask 서버 응답 그대로 클라이언트에 전달
            return ResponseEntity.status(response.getStatusCode()).body(response.getBody());

        } catch (IOException e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("파일 전송 실패");
        }
    }

    @GetMapping("/report/{subject}")
    public ResponseEntity<ByteArrayResource> downloadPdfReport(@PathVariable("subject") String subject) {
        return fileService.downloadSubjectReportPdf(subject);
    }




}
