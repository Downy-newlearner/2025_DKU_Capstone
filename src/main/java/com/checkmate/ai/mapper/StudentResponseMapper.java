package com.checkmate.ai.mapper;

import com.checkmate.ai.entity.Student;
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
    public StudentResponse toEntity(KafkaStudentResponseDto dto, Student student) {
        StudentResponse studentResponse = new StudentResponse();

        // 연관관계 설정
        studentResponse.setStudent(student);

        // 과목 설정
        studentResponse.setSubject(dto.getSubject());

        // 답안 변환
        List<ExamResponse> examResponses = dto.getAnswers().stream()
                .map(this::toExamResponse)
                .collect(Collectors.toList());

        studentResponse.setAnswers(examResponses);

        // 총점 설정
        studentResponse.setTotalScore(dto.getTotal_score());

        return studentResponse;
    }



    // KafkaStudentResponseDto.ExamResponseDto -> ExamResponse 변환
    private ExamResponse toExamResponse(KafkaStudentResponseDto.ExamResponseDto examResponseDto) {
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestionNumber(examResponseDto.getQuestion_number());
        examResponse.setStudentAnswer(examResponseDto.getStudent_answer());
        examResponse.setAnswerCount(examResponseDto.getAnswer_count());
        examResponse.setScore(examResponseDto.getScore());
        examResponse.setCorrect(examResponseDto.is_correct());
        examResponse.setConfidence(examResponseDto.getConfidence());
        return examResponse;
    }
}
