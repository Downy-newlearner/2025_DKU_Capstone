package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.dto.ExamResponseDto;
import org.springframework.stereotype.Component;

@Component
public class ExamResponseMapper {



    // ExamResponse -> ExamResponseDto 변환
    public ExamResponseDto toDto(ExamResponse examResponse) {
        ExamResponseDto dto = new ExamResponseDto();
        dto.setQuestion_number(examResponse.getQuestion_number());
        dto.setStudent_answer(examResponse.getStudent_answer());
        dto.setConfidence(examResponse.getConfidence());
        dto.set_correct(examResponse.is_correct());
        dto.setScore(examResponse.getScore());
        return dto;
    }

    public ExamResponse toEntity(KafkaStudentResponseDto.ExamResponseDto dto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestion_number(dto.getQuestionNumber());
        examResponse.setStudent_answer(dto.getStudentAnswer());
        examResponse.setConfidence(dto.getConfidence());
        examResponse.set_correct(dto.isCorrect());
        examResponse.setScore(dto.getScore());
        return examResponse;
    }

    // ExamResponseDto -> ExamResponse 변환
    public ExamResponse toEntity(ExamResponseDto dto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestion_number(dto.getQuestion_number());
        examResponse.setStudent_answer(dto.getStudent_answer());
        examResponse.setConfidence(dto.getConfidence());
        examResponse.set_correct(dto.is_correct());
        examResponse.setScore(dto.getScore());
        return examResponse;
    }

    // KafkaStudentResponseDto.ExamResponseDto -> ExamResponseDto 변환
    public ExamResponseDto toDto(KafkaStudentResponseDto.ExamResponseDto examResponseDto) {
        ExamResponseDto dto = new ExamResponseDto();

        // KafkaStudentResponseDto.ExamResponseDto에서 ExamResponseDto로 값 매핑
        dto.setQuestion_number(examResponseDto.getQuestionNumber());
        dto.setStudent_answer(examResponseDto.getStudentAnswer());
        dto.setConfidence(examResponseDto.getConfidence());
        dto.set_correct(examResponseDto.isCorrect());
        dto.setScore(examResponseDto.getScore());

        return dto;
    }
}

