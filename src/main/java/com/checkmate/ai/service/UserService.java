package com.checkmate.ai.service;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.mapper.UserMapper;
import com.checkmate.ai.repository.mongo.UserRepository;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
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
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {


    private final UserRepository userRepository;

    private final AuthenticationManagerBuilder authenticationManagerBuilder;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;
    private final JavaMailSender mailSender;
    private final RedisTemplate<String, String> redisTemplate;


    @Value("${app.reset-password.url}")
    private String resetPasswordUrl;

    @Value("${spring.mail.from}")
    private String mailFrom;

    @Transactional
    public String userSignup(SignUpDto signUpDto) {
        if (userRepository.findByEmail(signUpDto.getEmail()).isPresent()) {
            return "User ID already exists!";
        }

        String encodedPassword = passwordEncoder.encode(signUpDto.getPassword());
        User currentUser = new User(signUpDto.getEmail(), encodedPassword, signUpDto.getName());
        userRepository.save(currentUser);
        return "Sign-up successful";
    }

    @Transactional
    public JwtToken userSignin(SignInDto signInDto) {
        User user = userRepository.findByEmail(signInDto.getEmail())
                .orElseThrow(() -> new UsernameNotFoundException("이메일을 찾을 수 없습니다."));

        if (!passwordEncoder.matches(signInDto.getPassword(), user.getPassword())) {
            throw new BadCredentialsException("비밀번호가 일치하지 않습니다.");
        }

        UsernamePasswordAuthenticationToken authenticationToken =
                new UsernamePasswordAuthenticationToken(signInDto.getEmail(), signInDto.getPassword());

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

        // Use UserMapper to convert User to UserDto
        return UserMapper.toDto(currentUser.get());
    }

    public List<UserDto> getAllUsers() {
        return userRepository.findAll().stream()
                .map(UserMapper::toDto)  // Using UserMapper to convert User to UserDto
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

        if (!passwordEncoder.matches(request.getCurrent_password(), user.getPassword())) {
            log.warn("비밀번호 변경 실패: 현재 비밀번호 불일치");
            return false;
        }

        user.setPassword(passwordEncoder.encode(request.getNew_password()));
        userRepository.save(user);

        log.info("비밀번호 변경 성공: {}", user.getEmail());
        return true;
    }

    public boolean sendRedirectEmail(String toEmail, String token) {
        try {
            // 토큰을 포함한 비밀번호 재설정 링크 생성
            String resetLink = resetPasswordUrl + token;

            // Redis에 토큰 저장 (토큰과 만료 시간 설정)
            redisTemplate.opsForValue().set("password-reset:" + token, toEmail, 1, TimeUnit.HOURS);  // 1시간 유효

            // 이메일 전송 설정
            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(mailFrom); // 발신자 이메일 설정
            helper.setTo(toEmail);
            helper.setSubject("🔒 비밀번호 재설정 링크");
            helper.setText("<p>비밀번호를 재설정하려면 아래 링크를 클릭하세요:</p>"
                    + "<a href=\"" + resetLink + "\">비밀번호 재설정</a>", true);

            // 이메일 전송
            mailSender.send(message);
            log.info("비밀번호 재설정 이메일 전송 완료: {}", toEmail);
            return true;

        } catch (MessagingException e) {
            log.error("이메일 전송 실패", e);
            throw new RuntimeException("이메일 전송에 실패했습니다.");
        }
    }


    public void deleteAll() {
        userRepository.deleteAll();
    }



    @Transactional
    public boolean resetPassword(String token, String newPassword) {
        // Redis에서 유효한 토큰을 확인했다면, 해당 토큰에 대한 유저 정보를 가져옵니다
        String storedToken =  redisTemplate.opsForValue().get("password-reset:" + token);

        if (storedToken == null) {
            return false; // 유효하지 않으면 false 반환
        }

        // 유저 정보 찾기 (토큰에 저장된 이메일 또는 ID로)
        User user = userRepository.findByEmail(storedToken).orElseThrow(() -> new RuntimeException("사용자를 찾을 수 없습니다."));
        String encryptedPassword = passwordEncoder.encode(newPassword);
        // 비밀번호 변경 로직
        user.setPassword(encryptedPassword);  // 비밀번호 변경
        userRepository.save(user);  // DB에 저장

        // Redis에서 토큰 삭제
        redisTemplate.delete("password-reset:" + token);

        return true;
    }

    @Transactional
    public ResponseEntity<String> logout(HttpServletRequest request) {
        // HTTP 요청에서 토큰 추출
        String token = jwtTokenProvider.resolveToken(request);
        if (token == null) {
            log.warn("로그아웃 실패: 토큰이 존재하지 않음");
            return ResponseEntity.badRequest().body("토큰이 없습니다.");
        }

        // 토큰 유효성 검사
        if (!jwtTokenProvider.validateToken(token)) {
            log.warn("로그아웃 실패: 유효하지 않은 토큰");
            return ResponseEntity.badRequest().body("유효하지 않은 토큰입니다.");
        }

        try {
            // 만료 시간을 토대로 블랙리스트에 토큰 추가
            long expiration = jwtTokenProvider.getExpiration(token);
            redisTemplate.opsForValue().set(token, "blacklisted", expiration, TimeUnit.MILLISECONDS);

            // 로그아웃 성공 시 SecurityContext 비우기
            SecurityContextHolder.clearContext();

            log.info("로그아웃 성공: 토큰 블랙리스트 추가됨");
            return ResponseEntity.ok("로그아웃 되었습니다.");
        } catch (Exception e) {
            log.error("로그아웃 처리 중 오류 발생: {}", e.getMessage());
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body("로그아웃 처리 중 오류가 발생했습니다.");
        }
    }






}
