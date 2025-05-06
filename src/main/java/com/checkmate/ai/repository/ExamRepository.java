package com.checkmate.ai.repository;

import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.ExamResponse;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface ExamRepository extends MongoRepository<Exam, String> {
}
