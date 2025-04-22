package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
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
    public String UserSignup(@RequestBody SignUpDto signUpDto){
        String email = signUpDto.getEmail();
        String password = signUpDto.getPassword();
        String name = signUpDto.getName();
        String result = userService.UserSignup(email,password,name);
        log.info("회원가입 결과 :"+result);
        return result;
    }

    @PostMapping("/sign-in")
    public JwtToken UserSignin(@RequestBody SignInDto signInDto){

        String id = signInDto.getEmail();
        String password = signInDto.getPassword();

        JwtToken jwtToken = userService.UserSignin(id, password);

        if(jwtToken == null){
            log.info("인증 실패");
            return null;
        }else{
            log.info("로그인 성공");
            return jwtToken;
        }
    }


    @GetMapping("/user")
    public ResponseEntity<UserDto> getUser(){
        // 현재 인증된 사용자 정보 가져오기
        return ResponseEntity.ok(userService.getUser());
    }

    @GetMapping("/user/all")
    public List<User> getAllUsers() {

        return userService.getAllUsers();
    }

    @DeleteMapping("/user/all")
    public ResponseEntity<String> readAllUsers() {
        userService.deleteAll();
        return ResponseEntity.ok("✅ 모든 로그가 삭제되었습니다.");
    }






