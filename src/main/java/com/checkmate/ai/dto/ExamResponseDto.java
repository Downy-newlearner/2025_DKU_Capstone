package com.checkmate.ai.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class ExamResponseDto {
    private int question_number;
    private String student_answer;
    private int sub_question_number;
    private int answer_count;
    private float confidence;
    @JsonProperty("is_correct")
    private boolean is_correct;
    private float score;
}
