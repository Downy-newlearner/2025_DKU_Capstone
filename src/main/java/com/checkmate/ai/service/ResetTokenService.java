package com.checkmate.ai.service;

import com.checkmate.ai.entity.User;
import com.checkmate.ai.repository.UserRepository;
import com.checkmate.ai.service.JwtTokenProvider;
import io.jsonwebtoken.Claims;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Optional;

@Service
public class ResetTokenService {

    private final UserRepository userRepository;
    private final JwtTokenProvider jwtTokenProvider;

    @Autowired
    public ResetTokenService(UserRepository userRepository, JwtTokenProvider jwtTokenProvider) {
        this.userRepository = userRepository;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    public boolean verifyResetToken(String token) {
        Claims claims = jwtTokenProvider.verifyResetToken(token);  // 토큰 파싱

        if (claims == null) {
            // 토큰 파싱 실패한 경우
            return false;
        }

        String email = claims.getSubject(); // 토큰에서 이메일 정보 추출

        // 이메일을 사용하여 데이터베이스에서 해당 사용자 존재 여부 확인
        Optional<User> user = userRepository.findByEmail(email);
        return user.isPresent();  // 사용자가 존재하면 true 반환
    }
}
