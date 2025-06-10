package com.checkmate.ai.dto;

import lombok.Data;
import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
@Data
public class StudentIdUpdateRequest {
    private StudentIdUpdateDto studentIdUpdateDto;
    private ExamDto examDto;
}
