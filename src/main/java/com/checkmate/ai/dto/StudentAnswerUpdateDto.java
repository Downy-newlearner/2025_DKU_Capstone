package com.checkmate.ai.dto;

import lombok.Data;

@Data
public class StudentAnswerUpdateDto {
    private String student_id; // 학생 ID
    private int question_number; // 질문 번호
    private String student_answer; // 수정된 학생의 답변
}
