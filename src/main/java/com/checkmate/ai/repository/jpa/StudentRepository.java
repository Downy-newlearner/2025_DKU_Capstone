package com.checkmate.ai.repository.jpa;

import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.entity.Student;
import org.springframework.data.jpa.repository.JpaRepository;

public interface StudentRepository extends JpaRepository<Student, String> {
}
