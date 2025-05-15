package com.checkmate.ai.service;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.StudentAnswerUpdateDto;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.mapper.KafkaStudentResponseMapper;
import com.checkmate.ai.mapper.StudentResponseMapper;
import com.checkmate.ai.repository.StudentResponseRepository;
import lombok.extern.slf4j.Slf4j;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
public class StudentResponseService {



    @Autowired
    private RedissonClient redissonClient;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private StudentResponseRepository studentResponseRepository;

    @Autowired
    private QuestionService questionService;


    public int gradeWithAnswerChecking(KafkaStudentResponseDto dto, List<Question> questions) {
        int totalScore = 0;

        for (KafkaStudentResponseDto.ExamResponseDto answer : dto.getAnswers()) {
            Question question = questionService.findQuestionByNumber(questions, answer.getQuestion_number(), answer.getSub_question_number());

            if (question != null) {
                if (answer.getConfidence() >= 85) {
                    boolean correct = isAnswerCorrect(answer, question);
                    answer.set_correct(correct);
                    answer.setScore(correct ? question.getPoint() : 0);
                    totalScore += answer.getScore();
                } else {
                    answer.setScore(-1);
                }

                saveStudentResponse(dto.getStudent_id(), dto.getSubject(), answer);
            } else {
                log.warn("해당 질문을 찾을 수 없습니다: {}-{}", answer.getQuestion_number(), answer.getSub_question_number());
            }
        }

        return totalScore;
    }

    private void saveStudentResponse(String studentId, String subject, KafkaStudentResponseDto.ExamResponseDto answer) {
        Optional<StudentResponse> optional = studentResponseRepository.findByStudentIdAndSubject(studentId, subject);
        StudentResponse studentResponse = optional.orElseGet(() -> {
            StudentResponse newResponse = new StudentResponse();
            newResponse.setStudentId(studentId);
            newResponse.setSubject(subject);
            return newResponse;
        });

        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestionNumber(answer.getQuestion_number());
        examResponse.setSubQuestionNumber(answer.getSub_question_number());
        examResponse.setStudentAnswer(answer.getStudent_answer());
        examResponse.setAnswerCount(answer.getAnswer_count());
        examResponse.setConfidence(answer.getConfidence());
        examResponse.setCorrect(answer.is_correct());
        examResponse.setScore(answer.getScore());

        studentResponse.getAnswers().removeIf(a -> a.getQuestionNumber() == examResponse.getQuestionNumber()
                && a.getSubQuestionNumber() == examResponse.getSubQuestionNumber());
        studentResponse.getAnswers().add(examResponse);

        studentResponseRepository.save(studentResponse);
    }



    private boolean isAnswerCorrect(KafkaStudentResponseDto.ExamResponseDto answer, Question question) {
        return answer.getStudent_answer() != null &&
                answer.getStudent_answer().equalsIgnoreCase(question.getAnswer());
    }

    public int safeGradeWithAnswerChecking(KafkaStudentResponseDto dto, List<Question> questions) {
        String lockKey = "grading-lock:" + dto.getStudent_id() + ":" + dto.getSubject();
        RLock lock = redissonClient.getLock(lockKey);
        boolean locked = false;

        try {
            locked = lock.tryLock(5, 60, TimeUnit.SECONDS);
            if (!locked) {
                // 락 획득 실패 시 Redis 큐에 저장하여 재처리 예약
                redisTemplate.opsForList().rightPush("grading:pending", dto);
                log.info("채점이 지연되었으며 큐에 추가됨: {}", lockKey);
                return -1;
            }
            return gradeWithAnswerChecking(dto, questions);
        } catch (Exception e) {
            throw new RuntimeException("채점 중 오류 발생: " + e.getMessage());
        } finally {
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }



    public void updateStudentResponses(StudentAnswerUpdateDto dto) {
        String subject = dto.getSubject();
        List<StudentAnswerUpdateDto.StudentAnswers> studentAnswersList = dto.getStudentAnswersList();

        for (StudentAnswerUpdateDto.StudentAnswers studentAnswers : studentAnswersList) {
            Optional<StudentResponse> optionalResponse = studentResponseRepository.findByStudentIdAndSubject(studentAnswers.getStudent_id(), subject);

            if (optionalResponse.isPresent()) {
                StudentResponse response = optionalResponse.get();

                for (StudentAnswerUpdateDto.StudentAnswers.AnswerDto answerDto : studentAnswers.getAnswers()) {
                    response.getAnswers().stream()
                            .filter(a -> a.getQuestionNumber() == answerDto.getQuestion_number()
                                    && a.getSubQuestionNumber() == answerDto.getSub_question_number())
                            .findFirst()
                            .ifPresent(a -> {
                                a.setStudentAnswer(answerDto.getStudent_answer());

                                // 정답 가져오기 (exam 등에서 질문과 정답 정보를 미리 조회해둔 상태라고 가정)
                                Question question = questionService.findQuestionBySubjectAndNumber(subject, answerDto.getQuestion_number(), answerDto.getSub_question_number());

                                if (question != null) {
                                    String studentAnswer = answerDto.getStudent_answer();
                                    String correctAnswer = question.getAnswer();

                                    boolean correct = studentAnswer != null && correctAnswer != null &&
                                            studentAnswer.trim().replaceAll("\\s+", "").equalsIgnoreCase(correctAnswer.trim().replaceAll("\\s+", ""));

                                    a.setCorrect(correct);
                                } else {
                                    a.setCorrect(false);
                                }
                            });
                }


                studentResponseRepository.save(response);
            }
        }
    }


}