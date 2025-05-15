package com.checkmate.ai.entity;

import lombok.Builder;
import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.Id;


@Getter
@Setter
public class ExamResponse {
    @Id
    private Long id;  // 데이터베이스에서 식별할 ID

    private int questionNumber;
    private int subQuestionNumber;
    private String studentAnswer;
    private int answerCount;
    private int confidence;
    private boolean isCorrect;
    private int score;
}
