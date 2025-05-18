package com.checkmate.ai.repository;


import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.entity.LowConfidenceImage;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.List;
import java.util.Optional;

public interface LowConfidenceImageRepository extends MongoRepository<LowConfidenceImage, String> {
    Optional<LowConfidenceImage> findBySubject(String subject);

}
