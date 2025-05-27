package com.checkmate.ai.entity;

import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import lombok.Builder;
import lombok.Getter;
import lombok.Setter;


@Getter
@Setter
@Entity
public class ExamResponse {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long examResponseId;  // 데이터베이스에서 식별할 ID
    private int questionNumber;
    private int subQuestionNumber;
    private String studentAnswer;
    private int answerCount;
    private int confidence;
    private boolean isCorrect;
    private int score;



}
