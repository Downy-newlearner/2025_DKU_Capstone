package com.checkmate.ai.dto;

import lombok.Data;
import lombok.Getter;

import java.util.List;

@Data
@Getter
public class StudentIdUpdateGetImageDto {
    private String status;
    private String subject; // 과목
    private List<LowConfidenceImages> lowConfidenceImages;

    @Data
    @Getter
    public static class LowConfidenceImages{
        private String file_name;
        // Before : 인식 안된 것중에 Spring에게 넘어오는 이미지
        private String base64_data;

    }


}
