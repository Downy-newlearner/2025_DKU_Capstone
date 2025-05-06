package com.checkmate.ai.entity;

import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.Id;

@Getter
@Setter
public class ExamResponse {
    @Id
    private Long id;  // 데이터베이스에서 식별할 ID

    private int question_number;
    private String student_answer;
    private int confidence;
    private boolean is_correct;
    private int score;
}
