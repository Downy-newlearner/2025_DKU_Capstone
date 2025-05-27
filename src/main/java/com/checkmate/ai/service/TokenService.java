package com.checkmate.ai.service;

import com.checkmate.ai.entity.User;
import com.checkmate.ai.repository.mongo.UserRepository;
import io.jsonwebtoken.Claims;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class TokenService {
    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;
    private final RedisTemplate redisTemplate;

    public boolean verifyResetToken(String token) {
        // 토큰 파싱 및 유효성 검사

        Claims claims = jwtTokenProvider.verifyResetToken(token);  // 토큰 파싱 및 유효성 검사

        if (claims == null) {
            // 유효하지 않은 토큰
            return false;
        }

        // 토큰에서 이메일 추출
        String email = claims.getSubject();

        // 이메일을 사용하여 데이터베이스에서 해당 사용자가 존재하는지 확인
        Optional<User> user = userRepository.findByEmail(email);

        // 사용자 존재 여부 체크
        return user.isPresent(); // 사용자가 존재하면 true, 아니면 false
    }

    public boolean isTokenBlacklisted(String token) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(token));
    }

}
