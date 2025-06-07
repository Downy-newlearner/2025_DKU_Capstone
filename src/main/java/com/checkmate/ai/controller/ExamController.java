package com.checkmate.ai.controller;

import com.checkmate.ai.dto.ExamDto;

import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.mapper.ExamMapper;
import com.checkmate.ai.service.ExamService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/exams")
public class ExamController {

    @Autowired
    private ExamService examService;




    @PostMapping("/final")
    public ResponseEntity<?> saveExam(@RequestBody ExamDto examDto) {
        log.info("요청 받은 Exam DTO: {}", examDto);

        boolean success = examService.saveExam(examDto);
        if (!success) {
            return ResponseEntity
                    .badRequest()
                    .body(Map.of("error", "이미 존재하는 과목입니다: " + examDto.getSubject()));
        }

        return ResponseEntity.ok(examDto);
    }


    @PostMapping
    public ResponseEntity<?> showExam(@RequestBody ExamDto examDto) {
        log.info("요청 받은 Exam DTO: {}", examDto);
        if (examService.isSubjectDuplicate(examDto.getSubject())) {
            return ResponseEntity.badRequest()
                    .body(Map.of("error", "이미 존재하는 과목입니다: " + examDto.getSubject()));
        }
        return ResponseEntity.ok(examDto);
    }



    @GetMapping("/{id}")
    public ResponseEntity<ExamDto> getExam(@PathVariable Long id) {
        return ResponseEntity.ok(examService.getExamById(id));
    }

    @GetMapping()
    public ResponseEntity<List<ExamDto>> getExamsByEmail() {
        return ResponseEntity.ok(examService.getExamsByEmail());
    }

//    @GetMapping
//    public ResponseEntity<List<ExamDto>> getAllExams() {
//        return ResponseEntity.ok(examService.getAllExams());
//    }


}
