package com.checkmate.ai.service;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.ResetToken;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.mapper.UserMapper;
import com.checkmate.ai.repository.ResetTokenRepository;
import com.checkmate.ai.repository.UserRepository;
import io.jsonwebtoken.Claims;
import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
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
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;
    private final ResetTokenRepository resetTokenRepository;
    private final AuthenticationManagerBuilder authenticationManagerBuilder;
    private final JwtTokenProvider jwtTokenProvider;
    private final PasswordEncoder passwordEncoder;
    private final JavaMailSender mailSender;

    @Value("${app.reset-password.url}")
    private String resetPasswordUrl;

    @Value("${spring.mail.from}")
    private String mailFrom;

    @Transactional
    public String UserSignup(SignUpDto signUpDto) {
        if (userRepository.findByEmail(signUpDto.getEmail()).isPresent()) {
            return "User ID already exists!";
        }

        String encodedPassword = passwordEncoder.encode(signUpDto.getPassword());
        User currentUser = new User(signUpDto.getEmail(), encodedPassword, signUpDto.getName());
        userRepository.save(currentUser);
        return "Sign-up successful";
    }

    @Transactional
    public JwtToken UserSignin(SignInDto signInDto) {
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

    public boolean sendRedirectEmail(String toEmail,String token) {
        try {
            // 토큰을 포함한 비밀번호 재설정 링크 생성
            String resetLink = resetPasswordUrl + token;

            MimeMessage message = mailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(message, true, "UTF-8");
            helper.setFrom(mailFrom); // 발신자 이메일 설정
            helper.setTo(toEmail);
            helper.setSubject("🔒 비밀번호 재설정 링크");
            helper.setText("<p>비밀번호를 재설정하려면 아래 링크를 클릭하세요:</p>"
                    + "<a href=\"" + resetLink + "\">비밀번호 재설정</a>", true);

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
        // 토큰 유효성 검사
        Claims claims = jwtTokenProvider.verifyResetToken(token); // 토큰 파싱 및 유효성 검사

        if (claims == null) {
            log.warn("유효하지 않은 토큰");
            return false; // 유효하지 않은 토큰
        }

        // 토큰에서 이메일 추출
        String email = claims.getSubject();

        // 이메일에 해당하는 유저 찾기
        Optional<User> user = userRepository.findByEmail(email);

        if (user.isPresent()) {
            User existingUser = user.get();
            existingUser.setPassword(passwordEncoder.encode(newPassword)); // 비밀번호 암호화
            userRepository.save(existingUser); // 비밀번호 저장

            // 토큰을 사용한 후 삭제 (이미 사용된 토큰을 지움)
            Optional<ResetToken> resetToken = resetTokenRepository.findByToken(token);
            resetToken.ifPresent(resetTokenRepository::delete); // Optional이 비어있지 않으면 삭제

            log.info("비밀번호 변경 성공: {}", email);
            return true; // 비밀번호 변경 성공
        }

        log.warn("사용자가 존재하지 않음: {}", email);
        return false; // 유저가 없을 경우
    }

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

}

