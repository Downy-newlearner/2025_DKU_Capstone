package com.checkmate.ai.service;

import com.checkmate.ai.dto.ExamDto;
import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.mapper.ExamMapper;
import com.checkmate.ai.repository.ExamRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Slf4j
@Service
public class ExamService {

    @Autowired
    private ExamRepository examRepository;


    public boolean saveExam(ExamDto examDto) {
        if (isSubjectDuplicate(examDto.getSubject())) {
            return false;
        }

        Exam exam = ExamMapper.toEntity(examDto);
        exam.getQuestions().forEach(q ->
                log.info("문항 번호 {}의 answer_count: {}", q.getQuestion_number(), q.getAnswer_count())
        );
        examRepository.save(exam);
        return true;
    }


    public boolean isSubjectDuplicate(String subject) {
        List<Exam> exams = examRepository.findAllBySubject(subject);
        return !exams.isEmpty();
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


    public List<Exam> getExamsBySubject(String subject) {
        return examRepository.findAllBySubject(subject);
    }

    public List<Question> getQuestionsBySubject(String subject) {
        Optional<Exam> exam = examRepository.findBySubject(subject);
        if (exam.isEmpty()) {
            throw new RuntimeException("Exam not found for subject: " + subject);
        }
        return exam.get().getQuestions();
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




