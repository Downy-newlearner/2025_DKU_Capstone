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
        dto.setQuestion_number(examResponse.getQuestionNumber());
        dto.setStudent_answer(examResponse.getStudentAnswer());
        dto.setConfidence(examResponse.getConfidence());
        dto.set_correct(examResponse.isCorrect());
        dto.setScore(examResponse.getScore());
        return dto;
    }

    public ExamResponse toEntity(KafkaStudentResponseDto.ExamResponseDto dto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestionNumber(dto.getQuestion_number());
        examResponse.setStudentAnswer(dto.getStudent_answer());
        examResponse.setConfidence(dto.getConfidence());
        examResponse.setCorrect(dto.is_correct());
        examResponse.setScore(dto.getScore());
        return examResponse;
    }

    // ExamResponseDto -> ExamResponse 변환
    public ExamResponse toEntity(ExamResponseDto dto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestionNumber(dto.getQuestion_number());
        examResponse.setStudentAnswer(dto.getStudent_answer());
        examResponse.setConfidence(dto.getConfidence());
        examResponse.setCorrect(dto.is_correct());
        examResponse.setScore(dto.getScore());
        return examResponse;
    }

    // KafkaStudentResponseDto.ExamResponseDto -> ExamResponseDto 변환
    public ExamResponseDto toDto(KafkaStudentResponseDto.ExamResponseDto examResponseDto) {
        ExamResponseDto dto = new ExamResponseDto();

        // KafkaStudentResponseDto.ExamResponseDto에서 ExamResponseDto로 값 매핑
        dto.setQuestion_number(examResponseDto.getQuestion_number());
        dto.setStudent_answer(examResponseDto.getStudent_answer());
        dto.setConfidence(examResponseDto.getConfidence());
        dto.set_correct(examResponseDto.is_correct());
        dto.setScore(examResponseDto.getScore());

        return dto;
    }
}

