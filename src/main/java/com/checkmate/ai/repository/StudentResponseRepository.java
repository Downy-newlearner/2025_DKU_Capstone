package com.checkmate.ai.repository;

import com.checkmate.ai.entity.StudentResponse;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface StudentResponseRepository extends MongoRepository<StudentResponse, String> {

}
