package com.checkmate.ai.service;

import com.checkmate.ai.dto.Base64ImageDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;

@Service
public class FileService {

    @Value("${file.image-dir}")
    private String imageDir;

    @Value("${flask.server.url}")
    private String flaskReportUrl;

    private final RestTemplate restTemplate;

    public FileService(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    public List<Base64ImageDto> getLowConfidenceImages(String subject) {
        List<Base64ImageDto> imageList = new ArrayList<>();

        File dir = new File(imageDir);
        File[] files = dir.listFiles((d, name) ->
                name.endsWith(".png") || name.endsWith(".jpg") || name.endsWith(".jpeg"));

        if (files != null) {
            int count = 0;
            for (File file : files) {
                if (count >= 6) break;
                try {
                    byte[] imageBytes = Files.readAllBytes(file.toPath());
                    String encoded = Base64.getEncoder().encodeToString(imageBytes);
                    imageList.add(new Base64ImageDto(file.getName(), encoded));
                    count++;
                } catch (IOException e) {
                    System.err.println("이미지 읽기 실패: " + file.getName());
                }
            }
        } else {
            System.err.println("이미지 디렉토리를 찾을 수 없습니다: " + imageDir);
        }

        return imageList;
    }

    public ResponseEntity<ByteArrayResource> downloadSubjectReportPdf(String subject) {
        String reportUrl = flaskReportUrl + "/" + subject;

        HttpHeaders headers = new HttpHeaders();
        headers.setAccept(List.of(MediaType.APPLICATION_PDF));
        HttpEntity<Void> requestEntity = new HttpEntity<>(headers);

        ResponseEntity<byte[]> response = restTemplate.exchange(
                reportUrl,
                HttpMethod.GET,
                requestEntity,
                byte[].class
        );

        if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
            ByteArrayResource resource = new ByteArrayResource(response.getBody());

            HttpHeaders responseHeaders = new HttpHeaders();
            responseHeaders.setContentType(MediaType.APPLICATION_PDF);
            responseHeaders.setContentDisposition(ContentDisposition
                    .attachment()
                    .filename(subject + "_report.pdf")
                    .build());

            return new ResponseEntity<>(resource, responseHeaders, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(HttpStatus.BAD_GATEWAY);
        }
    }
}
