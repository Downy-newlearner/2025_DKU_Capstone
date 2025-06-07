package com.checkmate.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class LowConfidenceImageDto {

    private String subject;
    private List<Image> images;

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Image {
        private String student_id;
        private String file_name;
        private String base64_data;
        private int question_number;
        private int sub_question_number;
    }
}



