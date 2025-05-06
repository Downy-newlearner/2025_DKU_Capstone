package com.checkmate.ai.repository;

import com.checkmate.ai.entity.ResetToken;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface ResetTokenRepository extends MongoRepository<ResetToken, String> {
    Optional<ResetToken> findByToken(String token); // 토큰을 통해 리셋 토큰 조회
}
