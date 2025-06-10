package com.checkmate.ai.dto;

import lombok.Data;
import java.util.List;

@Data
public class StudentAnswerUpdateDto {
    private String subject; // 과목
    private List<StudentAnswers> studentAnswersList; // 여러 학생 답변 리스트

    @Data
    public static class StudentAnswers {
        private String student_id; // 학생 ID
        private List<AnswerDto> answers; // 여러 답변 리스트

        @Data
        public static class AnswerDto {
            private int question_number;
            private int sub_question_number;
            private String student_answer;

        }
    }
}
