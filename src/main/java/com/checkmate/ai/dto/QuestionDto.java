package com.checkmate.ai.dto;

import lombok.Data;

@Data
public class QuestionDto {
    private int question_number;
    private String question_type; // e.g. "short_answer", "TF", "descriptive"
    private int sub_question_number; // optional (null 허용)
    private int answer_count;
    private String answer;
    private float point;
}



