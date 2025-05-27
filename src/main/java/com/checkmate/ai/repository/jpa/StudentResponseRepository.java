package com.checkmate.ai.repository.jpa;

import com.checkmate.ai.entity.Student;
import com.checkmate.ai.entity.StudentResponse;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface StudentResponseRepository extends JpaRepository<StudentResponse, Long> {



//    Optional<StudentResponse> findByStudent_IdAndSubject(String studentId, String subject);


    List<StudentResponse> findBySubject(String subject);

    Optional<StudentResponse> findByStudentAndSubject(Student student, String subject);
}
