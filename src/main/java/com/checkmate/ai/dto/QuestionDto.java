package com.checkmate.ai.dto;

import lombok.Data;

@Data
public class QuestionDto {
    private int question_number;
    private String question_type; // e.g. "short_answer", "TF", "descriptive"
    private Integer sub_question_number; // optional (null 허용)
    private String answer;
    private int allocated_score;
}
