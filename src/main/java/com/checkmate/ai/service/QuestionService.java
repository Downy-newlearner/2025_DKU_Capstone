package com.checkmate.ai.service;

import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.repository.jpa.ExamRepository;
import com.checkmate.ai.repository.jpa.QuestionRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.TimeUnit;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.databind.SerializationFeature;

@Service
public class QuestionService {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .registerModule(new JavaTimeModule())
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    @Autowired
    private ExamRepository examRepository;

    @Autowired
    private RedisTemplate<String, String> redisTemplate;

    @Autowired
    private ExamService examService;




    private static final long CACHE_TTL = 1800; // 30분 TTL




    public Question findQuestionBySubjectAndNumber(String subject, int questionNumber, int subQuestionNumber) {

        Exam exam = examRepository.findBySubject(subject)
                .orElseThrow(() -> new RuntimeException("해당 과목 시험 정보가 없습니다."));

        return exam.getQuestions().stream()
                .filter(q -> q.getQuestionNumber() == questionNumber && q.getSubQuestionNumber() == subQuestionNumber)
                .findFirst()
                .orElse(null);
    }

    Question findQuestionByNumber(List<Question> questions, int questionNumber, int subQuestionNumber) {
        return questions.stream()
                .filter(q -> q.getQuestionNumber() == questionNumber && q.getSubQuestionNumber() == subQuestionNumber)
                .findFirst()
                .orElse(null);
    }



    public List<Question> getQuestionsFromCache(String subject) {
        ValueOperations<String, String> ops = redisTemplate.opsForValue();
        String cacheKey = "questions:" + subject;

        try {
            String cached = ops.get(cacheKey);
            if (cached != null) {
                return objectMapper.readValue(cached, new TypeReference<List<Question>>() {});
            }

            List<Question> questions = examService.getQuestionsBySubject(subject);
            String json = objectMapper.writeValueAsString(questions);
            ops.set(cacheKey, json, CACHE_TTL, TimeUnit.SECONDS);
            return questions;

        } catch (Exception e) {
            throw new RuntimeException("캐시 처리 중 오류", e);
        }
    }



    public void evictQuestionsCache(String subject) {
        redisTemplate.delete("questions:" + subject);
    }

}


