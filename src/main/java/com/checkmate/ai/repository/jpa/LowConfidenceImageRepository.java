package com.checkmate.ai.repository.jpa;


import com.checkmate.ai.entity.LowConfidenceImage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface LowConfidenceImageRepository extends JpaRepository<LowConfidenceImage, Long> {
    Optional<LowConfidenceImage> findBySubject(String subject);

}
