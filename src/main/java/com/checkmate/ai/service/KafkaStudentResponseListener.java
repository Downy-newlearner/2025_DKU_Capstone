package com.checkmate.ai.service;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.service.StudentResponseService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class KafkaStudentResponseListener {

    @Autowired
    private StudentResponseService studentResponseService;

    @Autowired
    private ExamService examService; // 문제 조회용 서비스 (예: DB에서 불러오기)

    private final ObjectMapper objectMapper = new ObjectMapper();

    @KafkaListener(topics = "student-responses", groupId = "exam-grading-group")
    public void listen(String message) {
        try {
            // 카프카로부터 받은 원본 메시지 출력
            System.out.println("수신된 메시지: " + message);

            // Kafka 메시지를 DTO로 역직렬화
            KafkaStudentResponseDto dto = objectMapper.readValue(message, KafkaStudentResponseDto.class);

            // DTO 내용 출력
            System.out.println("학생 ID: " + dto.getStudent_id());
            System.out.println("과목: " + dto.getSubject());
            System.out.println("전체 점수: " + dto.getTotal_score());

            // 문제 정보 조회
            List<Question> questions = examService.getQuestionsBySubject(dto.getSubject());

            // 자동 채점 실행
            int totalScore = studentResponseService.gradeWithAnswerChecking(dto, questions);

            System.out.println("채점 완료. 총점: " + totalScore);

        } catch (Exception e) {
            e.printStackTrace();
            System.err.println("Kafka 메시지 처리 중 오류 발생: " + e.getMessage());
        }
    }
}
