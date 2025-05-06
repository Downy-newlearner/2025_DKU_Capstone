package com.checkmate.ai.dto;

import lombok.Getter;
import lombok.Setter;

import java.util.List;


@Getter
@Setter
public class ReviewedAnswersRequest {
    private List<QuestionDto> questions;
    private List<KafkaStudentResponseDto.ExamResponseDto> reviewedAnswers;
    // getter, setter
}
