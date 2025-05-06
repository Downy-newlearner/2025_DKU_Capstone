package com.checkmate.ai.service;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.mapper.KafkaStudentResponseMapper;
import com.checkmate.ai.mapper.StudentResponseMapper;
import com.checkmate.ai.repository.StudentResponseRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;

// 서비스 클래스

@Service
public class StudentResponseService {

    @Autowired
    private StudentResponseRepository studentResponseRepository;

    @Autowired
    private StudentResponseMapper studentResponseMapper;

    @Autowired
    private KafkaStudentResponseMapper kafkaStudentResponseMapper;

    public boolean isAnswerCorrect(KafkaStudentResponseDto.ExamResponseDto answer, QuestionDto question) {
        return answer.getStudentAnswer() != null &&
                answer.getStudentAnswer().equalsIgnoreCase(question.getAnswer());
    }

    public int gradeWithAnswerChecking(KafkaStudentResponseDto dto, List<QuestionDto> questions) {
        int totalScore = 0;

        for (KafkaStudentResponseDto.ExamResponseDto answer : dto.getAnswers()) {
            QuestionDto question = findQuestionByNumber(questions, answer.getQuestionNumber());

            if (question != null) {
                if (answer.getConfidence() >= 85) {
                    if (isAnswerCorrect(answer, question)) {
                        answer.setScore(question.getPoint());
                        answer.setCorrect(true);
                    } else {
                        answer.setScore(0);
                        answer.setCorrect(false);
                    }
                    totalScore += answer.getScore();
                } else {
                    answer.setScore(-1); // 미채점 상태로 설정
                }

                saveStudentResponse(answer); // DB에 저장
            }
        }

        return totalScore;
    }

    public int gradeReviewedAnswers(List<KafkaStudentResponseDto.ExamResponseDto> reviewedAnswers, List<QuestionDto> questions) {
        int totalScore = 0;

        for (KafkaStudentResponseDto.ExamResponseDto answer : reviewedAnswers) {
            QuestionDto question = findQuestionByNumber(questions, answer.getQuestionNumber());

            if (question != null) {
                if (isAnswerCorrect(answer, question)) {
                    answer.setScore(question.getPoint());
                    answer.setCorrect(true);
                } else {
                    answer.setScore(0);
                    answer.setCorrect(false);
                }
                totalScore += answer.getScore();
            }
        }

        return totalScore;
    }

    private QuestionDto findQuestionByNumber(List<QuestionDto> questions, int questionNumber) {
        return questions.stream()
                .filter(q -> q.getQuestion_number() == questionNumber)
                .findFirst()
                .orElse(null);
    }

    private void saveStudentResponse(KafkaStudentResponseDto.ExamResponseDto answer) {
        // KafkaStudentResponseDto.ExamResponseDto를 StudentResponse로 변환 후 DB에 저장
        StudentResponse studentResponse = studentResponseMapper.toEntity(kafkaStudentResponseMapper.toDto(answer));
        studentResponseRepository.save(studentResponse); // DB에 저장
    }
}
