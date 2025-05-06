package com.checkmate.ai.controller;

import com.checkmate.ai.dto.ExamDto;

import com.checkmate.ai.service.ExamService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/exams")
public class ExamController {

    @Autowired
    private ExamService examService;

    @PostMapping("/final")
    public ResponseEntity<ExamDto> saveExam(@RequestBody ExamDto examDto) {
        log.info("요청 받은 Exam DTO: {}", examDto);
        examService.saveExam(examDto);
        return ResponseEntity.ok(examDto);
    }

    @PostMapping
    public ResponseEntity<ExamDto> showExam(@RequestBody ExamDto examDto) {
        log.info("요청 받은 Exam DTO: {}", examDto);
        return ResponseEntity.ok(examDto);
    }



    @GetMapping("/{id}")
    public ResponseEntity<ExamDto> getExam(@PathVariable String id) {
        return ResponseEntity.ok(examService.getExamById(id));
    }

    @GetMapping
    public ResponseEntity<List<ExamDto>> getAllExams() {
        return ResponseEntity.ok(examService.getAllExams());
    }


}
