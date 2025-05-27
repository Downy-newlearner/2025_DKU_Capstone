package com.checkmate.ai.dto;

import lombok.Data;
import java.time.LocalDateTime;
import java.util.List;


@Data
public class  ExamDto {
    private Long id;
    private String subject;
    private LocalDateTime exam_date;
    private List<QuestionDto> questions;
    private LocalDateTime created_at;
    private LocalDateTime update_at;
}
