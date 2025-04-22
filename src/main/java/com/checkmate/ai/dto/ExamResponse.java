package com.checkmate.ai.dto;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor

public class ExamResponse {
    private int question_number;
    private String student_answer;
    private int confidence;
    private boolean is_correct;
    private int score;
}
