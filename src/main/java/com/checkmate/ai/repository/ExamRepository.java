package com.checkmate.ai.repository;

import com.checkmate.ai.entity.Exam;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface ExamRepository extends MongoRepository<Exam, String> {
}
