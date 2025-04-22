package com.checkmate.ai.controller;

import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.service.ExamService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Optional;

@Slf4j
@RestController
@RequestMapping("/exams")
public class ExamController {

    @Autowired
    private ExamService examService;

    @PostMapping
    public ResponseEntity<String> saveExam(@RequestBody Exam exam) {
        log.info("요청 받은 Exam: {}", exam);
        examService.saveExam(exam);
        return ResponseEntity.ok("저장 완료");
    }

    @GetMapping("/{id}")
    public ResponseEntity<Optional<Exam>> getExam(@PathVariable String id) {
        Optional<Exam> exam = examService.getExamById(id);
        return ResponseEntity.ok(exam);
    }

    @GetMapping
    public ResponseEntity<List<Exam>> getAllExams() {
        return ResponseEntity.ok(examService.getAllExams());
    }


//    // 학생 응답 추가
//    @PutMapping("/{id}/responses")
//    public Exam submitStudentResponse(@PathVariable String id, @RequestBody StudentResponse studentResponse) {
//        return examService.addStudentResponse(id, studentResponse);
//    }
}
