package com.checkmate.ai.repository;

import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.entity.StudentResponse;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ExamResponseRepository extends MongoRepository<ExamResponse, String> {

}
