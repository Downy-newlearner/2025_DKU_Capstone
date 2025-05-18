package com.checkmate.ai.service;

import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.repository.ExamRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class QuestionService {

    @Autowired
    ExamRepository examRepository;


    public Question findQuestionBySubjectAndNumber(String subject, int questionNumber, int subQuestionNumber) {

        Exam exam = examRepository.findBySubject(subject)
                .orElseThrow(() -> new RuntimeException("해당 과목 시험 정보가 없습니다."));

        return exam.getQuestions().stream()
                .filter(q -> q.getQuestion_number() == questionNumber && q.getSub_question_number() == subQuestionNumber)
                .findFirst()
                .orElse(null);
    }

    Question findQuestionByNumber(List<Question> questions, int questionNumber, int subQuestionNumber) {
        return questions.stream()
                .filter(q -> q.getQuestion_number() == questionNumber && q.getSub_question_number() == subQuestionNumber)
                .findFirst()
                .orElse(null);
    }

}


