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
        dto.setId(exam.getId());
        dto.setSubject(exam.getSubject());
        dto.setExam_date(exam.getExamDate());
        dto.setCreated_at(exam.getCreatedAt());
        dto.setUpdate_at(exam.getUpdatedAt());

        List<QuestionDto> questionDtos = exam.getQuestions().stream().map(q -> {
            QuestionDto qdto = new QuestionDto();
            qdto.setQuestion_number(q.getQuestion_number());
            qdto.setQuestion_type(q.getQuestion_type());
            qdto.setSub_question_number(q.getSub_question_number());
            qdto.setAnswer(q.getAnswer());
            qdto.setPoint(q.getPoint());
            return qdto;
        }).collect(Collectors.toList());

        dto.setQuestions(questionDtos);
        return dto;
    }

    public static Exam toEntity(ExamDto dto) {
        Exam exam = new Exam();
        exam.setId(dto.getId());
        exam.setSubject(dto.getSubject());
        exam.setExamDate(dto.getExam_date());
        exam.setCreatedAt(dto.getCreated_at());
        exam.setUpdatedAt(dto.getUpdate_at());

        List<Question> questions = dto.getQuestions().stream().map(qdto -> {
            Question q = new Question();
            q.setQuestion_number(qdto.getQuestion_number());
            q.setQuestion_type(qdto.getQuestion_type());
            q.setSub_question_number(qdto.getSub_question_number());
            q.setAnswer(qdto.getAnswer());
            q.setPoint(qdto.getPoint());

            // answer_count 계산
            if (qdto.getAnswer() != null && !qdto.getAnswer().isBlank()) {
                int count = (int) Arrays.stream(qdto.getAnswer().split(","))
                        .map(String::trim)
                        .filter(s -> !s.isBlank())
                        .count();
                q.setAnswer_count(count);
            } else {
                q.setAnswer_count(0);
            }

            return q;
        }).collect(Collectors.toList());

        exam.setQuestions(questions);
        return exam;
    }


}
