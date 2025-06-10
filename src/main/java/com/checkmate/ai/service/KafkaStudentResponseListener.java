package com.checkmate.ai.service;


import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.StudentIdUpdateGetImageDto;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.Student;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.util.Base64;
import java.util.List;

@Service
@Slf4j
public class KafkaStudentResponseListener {




    @Autowired
    private StudentResponseService studentResponseService;

    @Autowired
    private LowConfidenceService lowConfidenceService;

    @Autowired
    private StudentService studentService;



    @Autowired
    private ExamService examService; // 문제 조회용 서비스 (예: DB에서 불러오기)

    private final ObjectMapper objectMapper = new ObjectMapper();
    @Autowired
    private QuestionService questionService;


    @KafkaListener(topics = "student-responses", groupId = "exam-grading-group")
    public void listen(String message) {
        try {
            System.out.println("📩 Kafka 채점 데이터:");
            System.out.println(" - Raw message: " + message);

            KafkaStudentResponseDto dto = objectMapper.readValue(message, KafkaStudentResponseDto.class);

            System.out.println("✅ DTO 변환 완료:");
            System.out.println(" - Student ID  : " + dto.getStudent_id());
            System.out.println(" - Student Name: " + dto.getStudent_name());

            // 1. 학생 정보 조회 또는 저장
            Student student = studentService.findById(dto.getStudent_id())
                    .orElseGet(() -> {
                        System.out.println("🔍 기존 학생 정보 없음. 새로 저장합니다.");
                        Student newStudent = new Student();
                        newStudent.setStudentId(dto.getStudent_id());
                        newStudent.setStudentName(dto.getStudent_name()); // dto에 학생 이름이 있다고 가정
                        Student saved = studentService.save(newStudent);
                        System.out.println("💾 학생 저장 완료: " + saved.getStudentId() + " - " + saved.getStudentName());
                        return saved;
                    });

            System.out.println("🎓 처리 중인 학생: " + student.getStudentId() + " - " + student.getStudentName());


            // 3. 안전한 자동 채점 수행 (Student 엔티티 전달 가능하도록 수정)
            float totalScore = studentResponseService.safeGradeWithAnswerChecking(dto, student);

            if (totalScore >= 0) {
                System.out.println("✅ 채점 완료 - 학생 ID: " + dto.getStudent_id() + ", 총점: " + totalScore);
            } else {
                System.out.println("⏳ 채점 지연 - 큐에 등록됨 (락 획득 실패)");
            }

        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("❌ Kafka 메시지 처리 중 오류 발생: " + e.getMessage());
        }
    }




    @KafkaListener(topics = "low-confidence-images", groupId = "image-saving-group")
    public void listenLowConfidenceImages(String message) {
        try {
            LowConfidenceImageDto imageDto = objectMapper.readValue(message, LowConfidenceImageDto.class);

            System.out.println("🖼️ 이미지 수신 - 과목: " + imageDto.getSubject());

            for (LowConfidenceImageDto.Image img : imageDto.getImages()) {
                System.out.println(" - Student ID      : " + img.getStudent_id());
                System.out.println(" - Question Number : " + img.getQuestion_number());
                System.out.println(" - Sub Question #  : " + img.getSub_question_number());
                System.out.println(" - File Name       : " + img.getFile_name());
                System.out.println("-----------------------------------");
            }



            System.out.println(("🖼️ 이미지 수신 - 과목: {}"+ imageDto.getSubject()));


            lowConfidenceService.saveImages(imageDto); // 내부에서 totalExpected 비교

            System.out.println("✅ 이미지 저장 완료 - 과목: {}"+ imageDto.getSubject());

        } catch (Exception e) {
            log.error("❌ Kafka 이미지 메시지 처리 중 오류", e);
        }
    }



}