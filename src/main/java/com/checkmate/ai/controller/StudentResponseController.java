package com.checkmate.ai.controller;

import com.checkmate.ai.dto.GradingRequestDto;
import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.dto.StudentAnswerUpdateDto;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.service.StudentResponseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@RestController
@RequestMapping("/responses")
public class StudentResponseController {

    @Autowired
    private StudentResponseService studentResponseService;


    @PostMapping("/grade-exam")
    public ResponseEntity<Integer> gradeExam(@RequestBody GradingRequestDto request) {
        int totalScore = studentResponseService.gradeWithAnswerChecking(
                request.getStudentResponse(), request.getQuestions());
        return ResponseEntity.ok(totalScore);
    }


    // 사용자 검토 후 재채점 처리
    @PostMapping("/reviewed-answers")
    public int gradeReviewedAnswers(@RequestBody List<KafkaStudentResponseDto.ExamResponseDto> reviewedAnswers, @RequestParam List<QuestionDto> questions) {
        return studentResponseService.gradeReviewedAnswers(reviewedAnswers, questions);
    }




//    // Create
//    @PostMapping
//    public ResponseEntity<StudentResponse> createStudentResponse(@RequestBody StudentResponse studentResponse) {
//        StudentResponse createdResponse = studentResponseService.createStudentResponse(studentResponse);
//        return ResponseEntity.ok(createdResponse);
//    }
//
//    // Read (All)
//    @GetMapping
//    public ResponseEntity<List<StudentResponse>> getAllStudentResponses() {
//        List<StudentResponse> studentResponses = studentResponseService.getAllStudentResponses();
//        return ResponseEntity.ok(studentResponses);
//    }
//
//    @PutMapping
//    public ResponseEntity<String> updateStudentResponse(@RequestBody StudentAnswerUpdateDto studentAnswerUpdateDto) {
//        Optional<StudentResponse> updatedStudentResponse = studentResponseService.updateStudentResponse(studentAnswerUpdateDto);
//
//        if (updatedStudentResponse.isPresent()) {
//            return ResponseEntity.ok("학생의 답변이 성공적으로 업데이트되었습니다.");
//        } else {
//            return ResponseEntity.status(404).body("학생 응답을 찾을 수 없습니다.");
//        }
//    }

}

