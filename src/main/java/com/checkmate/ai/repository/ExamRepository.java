package com.checkmate.ai.repository;

import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.ExamResponse;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface ExamRepository extends MongoRepository<Exam, String> {
    List<QuestionDto> findQuestionsBySubject(String subject);
    List<Exam> findAllBySubject(String subject);

    Optional<Exam> findBySubject(String subject);
}
