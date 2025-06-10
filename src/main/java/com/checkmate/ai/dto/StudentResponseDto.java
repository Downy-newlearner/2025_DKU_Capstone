package com.checkmate.ai.dto;

import lombok.Getter;

import lombok.Setter;

import java.util.List;
@Getter
@Setter
public class StudentResponseDto {
    private String student_id;
    private String subject;
    private List<ExamResponseDto> answers;
    private float total_score;
    // Getters, Setters, Constructors
}
