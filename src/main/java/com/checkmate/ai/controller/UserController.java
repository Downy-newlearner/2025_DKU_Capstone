package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequiredArgsConstructor
@Slf4j
public class UserController {
    private final UserService userService;

    @GetMapping("/test")
    public String test() {
        return "test";
    }

    @PostMapping("/sign-up")
    public ResponseEntity<String> userSignup(@RequestBody SignUpDto signUpDto) {
        String email = signUpDto.getEmail();
        String password = signUpDto.getPassword();
        String name = signUpDto.getName();
        String result = userService.UserSignup(email, password, name);
        log.info("회원가입 결과: {}", result);
        return ResponseEntity.ok(result);
    }

    @PostMapping("/sign-in")
    public ResponseEntity<JwtToken> userSignin(@RequestBody SignInDto signInDto) {
        String email = signInDto.getEmail();
        String password = signInDto.getPassword();

        JwtToken jwtToken = userService.UserSignin(email, password);
        if (jwtToken == null) {
            log.info("인증 실패");
            return ResponseEntity.badRequest().build();
        } else {
            log.info("로그인 성공");
            return ResponseEntity.ok(jwtToken);
        }
    }

    @PostMapping("/reset-request")
    public ResponseEntity<String> sendRedirectEmail(@RequestBody ResetRequestDto resetRequestDto) {
        boolean result = userService.sendRedirectEmail(resetRequestDto.getEmail());
        if (result) {
            return ResponseEntity.ok("📩 이메일이 성공적으로 전송되었습니다.");
        } else {
            return ResponseEntity.badRequest().body("❌ 이메일 전송에 실패하였습니다.");
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
