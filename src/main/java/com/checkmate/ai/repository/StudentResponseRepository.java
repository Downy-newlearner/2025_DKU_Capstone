package com.checkmate.ai.repository;

import com.checkmate.ai.entity.StudentResponse;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface StudentResponseRepository extends MongoRepository<StudentResponse, String> {



    Optional<StudentResponse> findByStudentIdAndSubject(String studentId, String subject);
}
