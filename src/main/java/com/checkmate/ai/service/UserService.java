package com.checkmate.ai.service;

import com.checkmate.ai.dto.JwtToken;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.config.annotation.authentication.builders.AuthenticationManagerBuilder;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {


    private final UserRepository userRepository;
    private final AuthenticationManagerBuilder authenticationManagerBuilder;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;



    @Transactional
    public String signUp(String email, String password, String name) {
        if (userRepository.findByEmail(email).isPresent()) {
            return "User ID already exists!";
        }

        String encodedPassword = passwordEncoder.encode(password); // 🔥 비밀번호 암호화
        User currentUser = new User(email, encodedPassword, name);
        userRepository.save(currentUser);


        return "Sign-up successful";
    }

    @Transactional
    public JwtToken signIn(String email, String rawPassword) { // ✅ email로 로그인
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("이메일을 찾을 수 없습니다."));

        // ✅ 비밀번호 검증 (평문 vs 암호화된 비밀번호 비교)
        if (!passwordEncoder.matches(rawPassword, user.getPassword())) {
            throw new BadCredentialsException("비밀번호가 일치하지 않습니다.");
        }

        // Spring Security 인증 처리
        UsernamePasswordAuthenticationToken authenticationToken =
                new UsernamePasswordAuthenticationToken(email, rawPassword);

        Authentication authentication;
        try {
            authentication = authenticationManagerBuilder.getObject().authenticate(authenticationToken);
        } catch (BadCredentialsException e) {
            log.error("인증 실패: {}", e.getMessage());
            return null;
        }

        if (!authentication.isAuthenticated()) {
            return null;
        }

        return jwtTokenProvider.generateToken(authentication);
    }


    public List<User> getAllUsers(){
        return userRepository.findAll();
    }

    public void deleteAll() {
        userRepository.deleteAll();
    }
}