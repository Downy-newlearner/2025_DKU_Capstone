package com.checkmate.ai.repository.jpa;

import com.checkmate.ai.entity.Question;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface QuestionRepository extends JpaRepository<Question, Long> {

    Question findByExamSubjectAndQuestionNumberAndSubQuestionNumber(
            String subject, int questionNumber, int subQuestionNumber);

}

