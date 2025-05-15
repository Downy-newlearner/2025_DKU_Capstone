package com.checkmate.ai.controller;

import com.checkmate.ai.dto.*;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.service.ExamService;
import com.checkmate.ai.service.StudentResponseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/responses")
public class StudentResponseController {




    @Autowired
    private StudentResponseService studentResponseService;


    @PutMapping
    public ResponseEntity<String> updateStudentResponses(@RequestBody StudentAnswerUpdateDto dto) {
        studentResponseService.updateStudentResponses(dto);
        return ResponseEntity.ok("여러 학생의 답변이 성공적으로 업데이트되었습니다.");
    }


}

