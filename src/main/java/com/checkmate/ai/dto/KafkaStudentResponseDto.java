package com.checkmate.ai.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import lombok.Getter;
import lombok.Setter;

import java.util.List;
@JsonIgnoreProperties(ignoreUnknown = true)
@Data
@Getter
@Setter
public class KafkaStudentResponseDto {
    @JsonProperty("student_id")
    private String student_id;
    private String student_name;
    private String subject;
    private List<ExamResponseDto> answers;  // 학생의 응답 목록
    private int total_score;  // 전체 점수

    @Data
    @Getter
    @Setter
    public static class ExamResponseDto {
        private int question_number;
        private int sub_question_number;
        private String student_answer;
        private int answer_count;
        private float confidence;
        private String question_type;

        @JsonProperty("is_correct")
        private boolean is_correct;
        private float score;
        private float point;  // 각 문제의 배점



    }
}



