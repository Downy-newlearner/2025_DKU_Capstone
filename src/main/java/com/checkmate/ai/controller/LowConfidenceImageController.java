package com.checkmate.ai.controller;

import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.service.LowConfidenceService;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.Map;
import java.util.Optional;

@RestController
public class LowConfidenceImageController {



    @Value("${flask.server.url}")
    private String flaskServerUrl;

    @Autowired
    private LowConfidenceService lowConfidenceService;

    @Autowired
    private RestTemplate restTemplate;


    // ZIP 파일 받아서 Flask 서버로 전송
    @PostMapping("/upload-zip")
    public ResponseEntity<String> uploadZipAndForwardToFlask(@RequestParam("file") MultipartFile zipFile) {
        if (zipFile.isEmpty()) {
            return ResponseEntity.badRequest().body("업로드된 파일이 없습니다.");
        }

        try {
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
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

            ResponseEntity<String> response = restTemplate.postForEntity(flaskServerUrl, requestEntity, String.class);

            return ResponseEntity.status(response.getStatusCode()).body(response.getBody());

        } catch (IOException e) {
            e.printStackTrace();
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("파일 전송 실패");
        }
    }

    @PostMapping("/images")
    public ResponseEntity<?> uploadImages(@RequestBody LowConfidenceImageDto dto) {

        boolean success = lowConfidenceService.saveImages(dto);
        if (!success) {
            return ResponseEntity
                    .badRequest()
                    .body(Map.of("error", "이미지 저장중 에러가 발생했습니다."));
        }
        return ResponseEntity.ok(dto);
    }


    @GetMapping("/images/check-status/{subject}")
    public ResponseEntity<?> getLowConfidenceStatus(@PathVariable String subject) {
        try {
            // Flask로 보낼 데이터 구성
            Map<String, String> requestBody = Map.of("subject", subject);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<Map<String, String>> requestEntity = new HttpEntity<>(requestBody, headers);

            // Flask로 POST 요청
            String requestUrl = flaskServerUrl + "/get-status";
            ResponseEntity<String> flaskResponse =
                    restTemplate.postForEntity(requestUrl, requestEntity, String.class);

            return ResponseEntity.ok(flaskResponse.getBody());  // React에 그대로 전달
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("Flask 요청 실패: " + e.getMessage());
        }
    }


    @GetMapping("/images/{subject}/low-confidence")
    public ResponseEntity<?> getBase64Images(@PathVariable String subject) {
        Optional<LowConfidenceImageDto> optionalImage = lowConfidenceService.getLowConfidenceImages(subject);

        if (optionalImage.isPresent()) {
            return ResponseEntity.ok(optionalImage.get());
        } else {
            return ResponseEntity
                    .status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "해당 subject에 대한 이미지가 없습니다: " + subject));
        }
    }






}
