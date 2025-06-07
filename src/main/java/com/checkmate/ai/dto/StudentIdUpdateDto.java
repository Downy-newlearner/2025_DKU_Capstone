package com.checkmate.ai.dto;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.util.List;

@Getter
@Data
public class StudentIdUpdateDto {
    private String subject; // 과목
    private List<student_list> student_list;

    @Getter
    @Setter
    @Data
    public static class student_list {
        private String student_id; // 학생 ID
        private String file_name;
        private String base64_data;
    }


}
