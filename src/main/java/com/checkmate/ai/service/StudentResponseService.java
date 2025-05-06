package com.checkmate.ai.service;

import com.checkmate.ai.dto.StudentAnswerUpdateDto;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.repository.StudentResponseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

@Service
public class StudentResponseService {

    @Autowired
    private StudentResponseRepository studentResponseRepository;

    // Create
    public StudentResponse createStudentResponse(StudentResponse studentResponse) {
        return studentResponseRepository.save(studentResponse);
    }

    // Read (By ID)
    public Optional<StudentResponse> getStudentResponseById(String id) {
        return studentResponseRepository.findById(id);
    }

    // Read (All)
    public List<StudentResponse> getAllStudentResponses() {
        return studentResponseRepository.findAll();
    }

    // Update method to modify the student response
    public Optional<StudentResponse> updateStudentResponse(StudentAnswerUpdateDto studentAnswerUpdateDto) {
        // 학생 ID와 질문 번호를 기반으로 해당 StudentResponse를 찾음
        Optional<StudentResponse> optionalStudentResponse = studentResponseRepository.findById(studentAnswerUpdateDto.getStudent_id());

        if (optionalStudentResponse.isPresent()) {
            StudentResponse studentResponse = optionalStudentResponse.get();

            // 해당 학생의 answers에서 질문 번호에 맞는 답변을 찾음
            studentResponse.getAnswers().stream()
                    .filter(answer -> answer.getQuestion_number() == studentAnswerUpdateDto.getQuestion_number())
                    .findFirst()
                    .ifPresent(answer -> {
                        // 답변을 수정
                        answer.setStudent_answer(studentAnswerUpdateDto.getStudent_answer());
                    });

            // 수정된 StudentResponse 저장
            return Optional.of(studentResponseRepository.save(studentResponse));
        }
        return Optional.empty();  // 해당 학생이 존재하지 않는 경우
    }

    // Delete
    public void deleteStudentResponse(String id) {
        studentResponseRepository.deleteById(id);
    }
}
