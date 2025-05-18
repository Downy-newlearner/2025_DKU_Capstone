package com.checkmate.ai.service;

import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.entity.Question;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
@Slf4j
public class KafkaStudentResponseListener {

    @Autowired
    private StudentResponseService studentResponseService;

    @Autowired
    LowConfidenceService lowConfidenceService;

    @Autowired
    private ExamService examService; // 문제 조회용 서비스 (예: DB에서 불러오기)

    private final ObjectMapper objectMapper = new ObjectMapper();



    @KafkaListener(topics = "student-responses", groupId = "exam-grading-group")
    public void listen(String message) {
        try {
            // Kafka 메시지 역직렬화
            KafkaStudentResponseDto dto = objectMapper.readValue(message, KafkaStudentResponseDto.class);

            System.out.println("수신된 메시지 - 학생 ID: " + dto.getStudent_id() + ", 과목: " + dto.getSubject());

            // 문제 정보 조회
            List<Question> questions = examService.getQuestionsBySubject(dto.getSubject());

            // Redis 기반 락을 사용한 안전한 자동 채점 수행
            int totalScore = studentResponseService.safeGradeWithAnswerChecking(dto, questions);

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

            log.info("🖼️ 이미지 수신 - 과목: {}", imageDto.getSubject());


            lowConfidenceService.saveImages(imageDto); // 내부에서 totalExpected 비교

            log.info("✅ 이미지 저장 완료 - 과목: {}", imageDto.getSubject());

        } catch (Exception e) {
            log.error("❌ Kafka 이미지 메시지 처리 중 오류", e);
        }
    }

}
