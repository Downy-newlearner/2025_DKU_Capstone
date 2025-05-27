package com.checkmate.ai.repository.jpa;

import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface ExamRepository extends JpaRepository<Exam, Long> {

    List<Exam> findAllByEmail(String email);

    List<Exam> findAllBySubject(String subject);


    Optional<Exam> findBySubject(String subject);
}
