package com.checkmate.ai.dto;

import lombok.Data;
import lombok.Getter;

import java.util.List;

@Data
@Getter
public class StudentIdUpdateGetImageDto {
    private String subject; // 과목
    private List<Image> images;

    @Data
    @Getter
    public static class Image{
        private String file_name;
        private String base64_data;

    }


}
