package com.checkmate.ai.mapper;

import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.ExamResponseDto;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class StudentResponseMapper {

    @Autowired
    private ExamResponseMapper examResponseMapper;

    // KafkaStudentResponseDto -> StudentResponse 변환
    public StudentResponse toEntity(KafkaStudentResponseDto dto) {
        StudentResponse studentResponse = new StudentResponse();
        studentResponse.setStudent_id(dto.getStudentId());
        studentResponse.setSubject(dto.getSubject());  // 과목명 설정

        // KafkaStudentResponseDto의 답안을 ExamResponse 객체로 변환
        List<ExamResponse> examResponses = dto.getAnswers().stream()
                .map(this::toExamResponse)  // ExamResponseDto를 변환
                .collect(Collectors.toList());

        studentResponse.setAnswers(examResponses);
        studentResponse.setTotal_score(dto.getTotalScore());  // 총점 설정
        return studentResponse;
    }



    // KafkaStudentResponseDto.ExamResponseDto -> ExamResponse 변환
    private ExamResponse toExamResponse(KafkaStudentResponseDto.ExamResponseDto examResponseDto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestion_number(examResponseDto.getQuestionNumber());
        examResponse.setStudent_answer(examResponseDto.getStudentAnswer());
        examResponse.setScore(examResponseDto.getScore());
        examResponse.set_correct(examResponseDto.isCorrect());
        examResponse.setConfidence(examResponseDto.getConfidence());
        return examResponse;
    }
}
