package com.checkmate.ai.service;

import com.checkmate.ai.dto.Base64ImageDto;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Objects;

@Service
public class FileService {

    @Value("${file.image-dir}")
    private String imageDir;

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
}
