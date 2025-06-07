package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.ExamDto;
import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.Question;

import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

public class ExamMapper {

    public static ExamDto toDto(Exam exam) {
        ExamDto dto = new ExamDto();
        dto.setId(exam.getExamId());
        dto.setSubject(exam.getSubject());
        dto.setExam_date(exam.getExamDate());
        dto.setCreated_at(exam.getCreatedAt());
        dto.setUpdate_at(exam.getUpdatedAt());

        List<QuestionDto> questionDtos = exam.getQuestions().stream().map(q -> {
            QuestionDto qdto = new QuestionDto();
            qdto.setQuestion_number(q.getQuestionNumber());
            qdto.setQuestion_type(q.getQuestionType());
            qdto.setSub_question_number(q.getSubQuestionNumber());
            qdto.setAnswer(q.getAnswer());
            qdto.setPoint(q.getPoint());

            // ⬇️ answer_count: answer 기준으로 쉼표로 구분하여 계산
            if (q.getAnswer() != null && !q.getAnswer().isBlank()) {
                int count = (int) Arrays.stream(q.getAnswer().split(","))
                        .map(String::trim)
                        .filter(s -> !s.isBlank())
                        .count();
                qdto.setAnswer_count(count);
            } else {
                qdto.setAnswer_count(0);
            }

            return qdto;
        }).collect(Collectors.toList());

        dto.setQuestions(questionDtos);
        return dto;
    }

    public static Exam toEntity(ExamDto dto, String email) {
        Exam exam = new Exam();
        exam.setExamId(dto.getId());
        exam.setSubject(dto.getSubject());
        exam.setExamDate(dto.getExam_date());
        exam.setCreatedAt(dto.getCreated_at());
        exam.setUpdatedAt(dto.getUpdate_at());
        exam.setEmail(email);

        List<Question> questions = dto.getQuestions().stream().map(qdto -> {
            Question q = new Question();
            q.setQuestionNumber(qdto.getQuestion_number());
            q.setQuestionType(qdto.getQuestion_type());
            q.setSubQuestionNumber(qdto.getSub_question_number());
            q.setAnswer(qdto.getAnswer());
            q.setPoint(qdto.getPoint());

            // ⬇️ answerCount: answer 기준으로 쉼표로 구분하여 계산
            if (qdto.getAnswer() != null && !qdto.getAnswer().isBlank()) {
                int count = (int) Arrays.stream(qdto.getAnswer().split(","))
                        .map(String::trim)
                        .filter(s -> !s.isBlank())
                        .count();
                q.setAnswerCount(count);
            } else {
                q.setAnswerCount(0);
            }

            q.setExam(exam);  // 양방향 연관관계 설정
            return q;
        }).collect(Collectors.toList());

        exam.setQuestions(questions);
        return exam;
    }
}
