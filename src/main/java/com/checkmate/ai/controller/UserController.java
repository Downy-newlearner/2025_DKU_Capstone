package com.checkmate.ai.controller;
import com.checkmate.ai.dto.*;
import com.checkmate.ai.service.JwtTokenProvider;
import com.checkmate.ai.service.TokenService;
import com.checkmate.ai.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;


@RestController
@RequiredArgsConstructor
@Slf4j
public class UserController {
    private final UserService userService;
    private final JwtTokenProvider jwtTokenProvider;
    private final RedisTemplate redisTemplate;
    private final TokenService tokenService;
    private final RestTemplate restTemplate;

    @GetMapping("/test")
    public String test() {
        // Flask 서버의 IP 주소나 도커 환경에 따라 조정
        String flaskUrl = "http://220.149.231.136:9054/hello";
        return restTemplate.getForObject(flaskUrl, String.class);
    }
    @PostMapping("/sign-up")
    public ResponseEntity<String> userSignup(@RequestBody SignUpDto signUpDto) {
        String result = userService.userSignup(signUpDto);
        log.info("회원가입 결과: {}", result);
        return ResponseEntity.ok(result);
    }


    @PostMapping("/sign-in")
    public ResponseEntity<JwtToken> userSignin(@RequestBody SignInDto signInDto, HttpSession session) {
        JwtToken jwtTokenDto = userService.userSignin(signInDto);

        if (jwtTokenDto == null) {
            log.info("인증 실패");
            return ResponseEntity.badRequest().build();
        } else {
            log.info("로그인 성공");

            // 세션에 사용자 이메일 저장
            session.setAttribute("userEmail", signInDto.getEmail());

            return ResponseEntity.ok(jwtTokenDto);
        }
    }


    @PostMapping("/logout")
    public ResponseEntity<String> logout(HttpServletRequest request) {
        return userService.logout(request);
    }





    @PostMapping("/reset-request")
    public ResponseEntity<String> sendResetPasswordEmail(@RequestBody ResetRequestDto resetRequestDto) {
        String email = resetRequestDto.getEmail();

        // JWT 토큰 생성
        String token = jwtTokenProvider.generateResetPasswordToken(email);

        // 이메일 전송
        boolean emailSent = userService.sendRedirectEmail(email, token);
        if (emailSent) {
            return ResponseEntity.ok("이메일이 성공적으로 전송되었습니다.");
        } else {
            return ResponseEntity.badRequest().body("이메일 전송에 실패했습니다.");
        }
    }

    @PostMapping("/reset-password")
    public ResponseEntity<String> resetPassword(@RequestBody PasswordChangeRequest resetRequestDto) {
        String token = resetRequestDto.getToken();
        String newPassword = resetRequestDto.getNew_password();

        // 토큰 검증
        boolean isTokenValid = tokenService.verifyResetToken(token);
        if (!isTokenValid) {
            return ResponseEntity.badRequest().body("잘못된 토큰입니다. 토큰이 만료되었거나 유효하지 않습니다.");
        }

        // 비밀번호 업데이트
        boolean isUpdated = userService.resetPassword(token, newPassword);
        if (isUpdated) {
            return ResponseEntity.ok("비밀번호가 성공적으로 변경되었습니다.");
        } else {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body("비밀번호 변경에 실패했습니다. 유저가 존재하지 않거나 오류가 발생했습니다.");
        }
    }


    @GetMapping("/user")
    public ResponseEntity<UserDto> getUser() {
        return ResponseEntity.ok(userService.getUser());
    }

    @GetMapping("/user/all")
    public ResponseEntity<List<UserDto>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }

    @PostMapping("/change-password")
    public ResponseEntity<String> changePassword(@RequestBody PasswordChangeRequest request) {
        boolean success = userService.changePassword(request);
        if (success) {
            return ResponseEntity.ok("비밀번호가 성공적으로 변경되었습니다.");
        } else {
            return ResponseEntity.badRequest().body("현재 비밀번호가 일치하지 않거나 사용자 정보를 찾을 수 없습니다.");
        }
    }

    @DeleteMapping("/user/all")
    public ResponseEntity<String> deleteAllUsers() {
        userService.deleteAll();
        return ResponseEntity.ok("✅ 모든 유저 정보가 삭제되었습니다.");
    }
}
