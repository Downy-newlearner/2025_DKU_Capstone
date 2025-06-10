package com.checkmate.ai.dto;

import lombok.*;

import java.time.LocalDateTime;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Getter
@Setter
public class LowConfidenceImageDto {

    private String subject;
    private LocalDateTime exam_date;
    private List<Image> images;

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    @Getter
    @Setter
    public static class Image {
        private String student_id;
        private String file_name;
        private String base64_data;
        private int question_number;
        private int sub_question_number;
    }
}



