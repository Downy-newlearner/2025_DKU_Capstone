package com.checkmate.ai.service;

import com.checkmate.ai.dto.ExamDto;
import com.checkmate.ai.dto.StudentAnswerUpdateDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.mapper.ExamMapper;
import com.checkmate.ai.repository.ExamRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class ExamService {

    @Autowired
    private ExamRepository examRepository;


    public void saveExam(ExamDto examDto) {
        Exam exam = ExamMapper.toEntity(examDto);
        examRepository.save(exam);
    }

    public ExamDto getExamById(String id) {
        return examRepository.findById(id)
                .map(ExamMapper::toDto)
                .orElseThrow(() -> new RuntimeException("Exam not found: " + id));
    }

    public List<ExamDto> getAllExams() {
        return examRepository.findAll().stream()
                .map(ExamMapper::toDto)
                .toList();
    }


}



//    public Exam addStudentResponse(String examId, StudentResponse newResponse) {
//        Optional<Exam> optionalExam = examRepository.findById(examId);
//        if (optionalExam.isPresent()) {
//            Exam exam = optionalExam.get();
//
//            // 기존 응답 중 동일 학생이 있으면 덮어쓰기
//            exam.getResponses().removeIf(r -> r.getStudentId().equals(newResponse.getStudentId()));
//            exam.getResponses().add(newResponse);
//
//            return examRepository.save(exam);
//        }
//        throw new RuntimeException("시험을 찾을 수 없습니다: " + examId);
//    }




