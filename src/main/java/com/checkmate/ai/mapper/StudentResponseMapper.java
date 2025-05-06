package com.checkmate.ai.mapper;

import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.dto.StudentResponseDto;
import com.checkmate.ai.dto.ExamResponseDto;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class StudentResponseMapper {

    // Entity -> DTO 변환
    public StudentResponseDto toDto(StudentResponse studentResponse) {
        StudentResponseDto dto = new StudentResponseDto();
        dto.setStudent_id(studentResponse.getStudent_id());

        // ExamResponse 객체들을 ExamResponseDto로 변환
        List<ExamResponseDto> examResponseDtos = studentResponse.getAnswers().stream()
                .map(this::toExamResponseDto) // ExamResponse -> ExamResponseDto 변환
                .collect(Collectors.toList());

        dto.setAnswers(examResponseDtos);
        return dto;
    }

    // ExamResponse -> ExamResponseDto 변환
    private ExamResponseDto toExamResponseDto(ExamResponse examResponse) {
        ExamResponseDto dto = new ExamResponseDto();
        dto.setQuestion_number(examResponse.getQuestion_number());
        dto.setStudent_answer(examResponse.getStudent_answer());
        dto.setConfidence(examResponse.getConfidence());
        dto.set_correct(examResponse.is_correct());
        dto.setScore(examResponse.getScore());
        return dto;
    }

    // DTO -> Entity 변환
    public StudentResponse toEntity(StudentResponseDto dto) {
        StudentResponse studentResponse = new StudentResponse();
        studentResponse.setStudent_id(dto.getStudent_id());

        // ExamResponseDto -> ExamResponse 변환 처리
        List<ExamResponse> examResponses = dto.getAnswers().stream()
                .map(this::toExamResponse)
                .collect(Collectors.toList());

        studentResponse.setAnswers(examResponses);
        return studentResponse;
    }

    // ExamResponseDto -> ExamResponse 변환
    private ExamResponse toExamResponse(ExamResponseDto dto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestion_number(dto.getQuestion_number());
        examResponse.setStudent_answer(dto.getStudent_answer());
        examResponse.setConfidence(dto.getConfidence());
        examResponse.set_correct(dto.is_correct());
        examResponse.setScore(dto.getScore());
        return examResponse;
    }
}
