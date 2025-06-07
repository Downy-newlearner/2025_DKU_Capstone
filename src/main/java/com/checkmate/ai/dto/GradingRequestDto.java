package com.checkmate.ai.dto;


import lombok.Data;

import java.util.List;

// Test를 위한 Dto
@Data
public class GradingRequestDto {
    private KafkaStudentResponseDto studentResponse;
    private List<QuestionDto> questions;
}
