package com.checkmate.ai.dto;

import lombok.Data;

import java.util.List;

@Data
public class KafkaStudentResponseDto {
    private String studentId;
    private String subject;
    private List<ExamResponseDto> answers;  // 학생의 응답 목록
    private int totalScore;  // 전체 점수

    @Data
    public static class ExamResponseDto {
        private int questionNumber;
        private Integer subQuestionNumber;
        private String studentAnswer;
        private int confidence;
        private boolean isCorrect;
        private int score;
        private String expectedAnswer;  // 예상 답안
        private int point;  // 각 문제의 배점


    }
}
