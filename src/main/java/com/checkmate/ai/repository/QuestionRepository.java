package com.checkmate.ai.repository;

import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.User;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface QuestionRepository extends MongoRepository<Question, String>{

}
