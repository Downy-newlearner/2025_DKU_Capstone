package com.checkmate.ai.service;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.mapper.UserMapper;
import com.checkmate.ai.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
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
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final AuthenticationManagerBuilder authenticationManagerBuilder;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public String UserSignup(String email, String password, String name) {
        if (userRepository.findByEmail(email).isPresent()) {
            return "User ID already exists!";
        }

        String encodedPassword = passwordEncoder.encode(password);
        User currentUser = new User(email, encodedPassword, name);
        userRepository.save(currentUser);
        return "Sign-up successful";
    }

    @Transactional
    public JwtToken UserSignin(String email, String rawPassword) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("이메일을 찾을 수 없습니다."));

        if (!passwordEncoder.matches(rawPassword, user.getPassword())) {
            throw new BadCredentialsException("비밀번호가 일치하지 않습니다.");
        }

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

    public UserDto getUser() {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        Optional<User> currentUser = userRepository.findByEmail(userDetails.getEmail());

        if (currentUser.isEmpty()) {
            log.info("조회된 User가 없습니다");
            return null;
        }

        return UserMapper.toDto(currentUser.get());
    }

    public List<UserDto> getAllUsers() {
        return userRepository.findAll().stream()
                .map(UserMapper::toDto)
                .collect(Collectors.toList());
    }

    public boolean changePassword(PasswordChangeRequest request) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        Optional<User> optionalUser = userRepository.findByEmail(userDetails.getEmail());

        if (optionalUser.isEmpty()) {
            log.warn("비밀번호 변경 실패: 사용자 정보 없음");
            return false;
        }

        User user = optionalUser.get();

        if (!passwordEncoder.matches(request.getCurrentPassword(), user.getPassword())) {
            log.warn("비밀번호 변경 실패: 현재 비밀번호 불일치");
            return false;
        }

        user.setPassword(passwordEncoder.encode(request.getNewPassword()));
        userRepository.save(user);

        log.info("비밀번호 변경 성공: {}", user.getEmail());
        return true;
    }

    public void deleteAll() {
        userRepository.deleteAll();
    }
}
