package com.checkmate.ai.dto;

import lombok.Getter;

import lombok.Setter;

import java.util.List;
@Getter
@Setter

public class StudentResponse {
    private String student_id;
    private List<ExamResponse> answers;

    // Getters, Setters, Constructors
}
