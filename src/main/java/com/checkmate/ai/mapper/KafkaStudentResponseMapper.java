package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.entity.Student;
import com.checkmate.ai.entity.StudentResponse;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.stream.Collectors;

@Component
public class KafkaStudentResponseMapper {

    // KafkaStudentResponseDto.ExamResponseDto를 KafkaStudentResponseDto로 변환
    public KafkaStudentResponseDto toDto(KafkaStudentResponseDto.ExamResponseDto answer) {
        KafkaStudentResponseDto dto = new KafkaStudentResponseDto();
        // `answer`를 `answers` 리스트로 설정
        dto.setAnswers(List.of(answer));

        // 예시로 studentId, subject 설정 필요시 추가 설정 가능
        // 예: dto.setStudentId(answer.getStudentId());
        // 예: dto.setSubject(answer.getSubject());

        return dto;
    }

    // KafkaStudentResponseDto.ExamResponseDto를 StudentResponse 엔티티로 변환
    public StudentResponse toEntity(KafkaStudentResponseDto dto, Student student)
    {
        StudentResponse entity = new StudentResponse();

        // StudentResponse의 studentId와 subject 설정
        entity.setStudent(student);  // Student 객체를 파라미터로 받아야 함

        entity.setSubject(dto.getSubject());

        // ExamResponse 리스트 설정
        List<ExamResponse> examResponses = dto.getAnswers().stream()
                .map(this::convertToExamResponse)
                .collect(Collectors.toList());

        entity.setAnswers(examResponses);

        // total_score 설정 (예시로 전체 점수는 각 ExamResponse의 점수를 합산하여 계산)
        float totalScore = examResponses.stream()
                .map(ExamResponse::getScore)
                .reduce(0f, Float::sum);

        entity.setTotalScore(totalScore);

        return entity;
    }

    // ExamResponseDto를 ExamResponse 엔티티로 변환
    private ExamResponse convertToExamResponse(KafkaStudentResponseDto.ExamResponseDto answer) {
        ExamResponse examResponse = new ExamResponse();

        examResponse.setQuestionNumber(answer.getQuestion_number());
        examResponse.setSubQuestionNumber(answer.getSub_question_number());
        examResponse.setStudentAnswer(answer.getStudent_answer());
        examResponse.setAnswerCount(answer.getAnswer_count());
        examResponse.setConfidence(answer.getConfidence());
        examResponse.setCorrect(answer.is_correct());
        examResponse.setScore(answer.getScore());

        return examResponse;
    }
}
