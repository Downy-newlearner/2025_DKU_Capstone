package com.checkmate.ai.entity;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class Question {

    private int question_number;
    private String question_type; // e.g. "short_answer", "TF", "descriptive"
    private int sub_question_number; // optional (null 허용)
    private String answer;
    private int allocated_score;
}
