package com.checkmate.ai.service;

import com.checkmate.ai.dto.StudentIdUpdateDto;
import com.checkmate.ai.entity.Student;
import com.checkmate.ai.repository.jpa.StudentRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.*;


@Slf4j
@Service
public class StudentService {

    @Value("${file.image-dir}")
    private String imageDirPath;

    @Autowired
    private StudentRepository studentRepository;



    public Optional<Student> findById(String id) {
        return studentRepository.findById(id);
    }
    public Student save(Student student) {
        return studentRepository.save(student);
    }


    public StudentIdUpdateDto renameFilesWithStudentId(StudentIdUpdateDto dto) {
        String subject = dto.getSubject();


        for (StudentIdUpdateDto.student_list student : dto.getStudent_list()) {
            String studentId = student.getStudent_id();
            String originalFileName = student.getFile_name();

            // 파일명이 비어 있으면 기본값 설정
            String baseFileName = (originalFileName == null || originalFileName.isEmpty()) ? "_" : originalFileName;

            String newFileName = baseFileName + "_" + subject + "_" + studentId + ".jpg";

            student.setFile_name(newFileName);

        }
            return dto;
        }




    public Student getStudentById(String studentId) {
        Optional <Student> studentOpt =  studentRepository.findById(studentId);
        Student student = studentOpt.get();
        return student;

    }


}
