package com.checkmate.ai.service;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import com.checkmate.ai.dto.StudentAnswerUpdateDto;
import com.checkmate.ai.dto.ZipListDto;
import com.checkmate.ai.entity.*;
import com.checkmate.ai.repository.jpa.StudentResponseRepository;
import lombok.extern.slf4j.Slf4j;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Slf4j
@Service
public class StudentResponseService {


    @Value("${custom.file.base-url}")
    private String fileBaseUrl;


    @Autowired
    private RedissonClient redissonClient;

    @Autowired
    private RedisTemplate<String, Object> redisTemplate;

    @Autowired
    private StudentResponseRepository studentResponseRepository;

    @Autowired
    private QuestionService questionService;
    @Autowired
    private StudentService studentService;
    @Autowired
    private ExamService examService;


    public List<StudentResponse> getStudentResponses(String subject) {
        return studentResponseRepository.findBySubject(subject);
    }


    public List<ZipListDto> getStudentResponseZiplist(String subject) {
        List<StudentResponse> responses = studentResponseRepository.findBySubject(subject);
        return responses.stream()
                .map(response -> {
                    Student student = response.getStudent();
                    String studentId = student.getStudentId();
                    String studentName = student.getStudentName();
                    String fileName = subject + "_" + studentId + "_" + studentName + ".zip";
                    String downloadUrl = fileBaseUrl + fileName;
                    return new ZipListDto(fileName, downloadUrl);
                })
                .collect(Collectors.toList());
    }



    public float gradeWithAnswerChecking(KafkaStudentResponseDto dto, List<Question> questions, Student student) {
        float totalScore = 0;

        for (KafkaStudentResponseDto.ExamResponseDto answer : dto.getAnswers()) {
            Question question = questionService.findQuestionBySubjectAndNumber(
                    dto.getSubject(), answer.getQuestion_number(), answer.getSub_question_number());

            if (question != null) {
                if (answer.getConfidence() >= 0.85) {
                    boolean correct = isAnswerCorrect(answer, question);
                    answer.set_correct(correct);
                    answer.setScore(correct ? question.getPoint() : 0);
                    totalScore += answer.getScore();
                } else {
                    answer.setScore(-1);
                }

                saveStudentResponse(student, dto.getSubject(), answer);
            } else {
                log.warn("문제를 찾을 수 없습니다. subject={}, qn={}, sqn={}",
                        dto.getSubject(), answer.getQuestion_number(), answer.getSub_question_number());
            }
        }

        return totalScore;
    }




    private void saveStudentResponse(Student student, String subject, KafkaStudentResponseDto.ExamResponseDto answer) {
        // Student 엔티티와 subject를 기준으로 StudentResponse 조회
        Optional<StudentResponse> optional = studentResponseRepository.findByStudentAndSubject(student, subject);

        StudentResponse studentResponse = optional.orElseGet(() -> {
            StudentResponse newResponse = new StudentResponse();
            newResponse.setStudent(student);  // ✅ 연관관계 설정
            newResponse.setSubject(subject);
            return newResponse;
        });

        // 기존 답변 중 같은 문제/서브문제 번호 제거
        studentResponse.getAnswers().removeIf(a -> a.getQuestionNumber() == answer.getQuestion_number()
                && a.getSubQuestionNumber() == answer.getSub_question_number());

        // 새로운 응답 추가
        ExamResponse examResponse = new ExamResponse();
        examResponse.setQuestionNumber(answer.getQuestion_number());
        examResponse.setSubQuestionNumber(answer.getSub_question_number());
        examResponse.setStudentAnswer(answer.getStudent_answer());
        examResponse.setAnswerCount(answer.getAnswer_count());
        examResponse.setConfidence(answer.getConfidence());
        examResponse.setCorrect(answer.is_correct());
        examResponse.setScore(answer.getScore());

        studentResponse.getAnswers().add(examResponse);

        // 총점 재계산
        float totalScore = studentResponse.getAnswers().stream()
                .map(ExamResponse::getScore)
                .reduce(0f, Float::sum);

        studentResponse.setTotalScore(totalScore);

        // 저장
        studentResponseRepository.save(studentResponse);
    }



    private boolean isAnswerCorrect(KafkaStudentResponseDto.ExamResponseDto answerDto, Question question) {
        String correctAnswer = question.getAnswer();
        String studentAnswer = answerDto.getStudent_answer();
        return correctAnswer != null
                && studentAnswer != null
                && correctAnswer.trim().equalsIgnoreCase(studentAnswer.trim());
    }


    public float safeGradeWithAnswerChecking(KafkaStudentResponseDto dto, Student student) {
        String lockKey = "grading-lock:" + dto.getStudent_id() + ":" + dto.getSubject();
        RLock lock = redissonClient.getLock(lockKey);
        boolean locked = false;

        try {
            locked = lock.tryLock(5, 60, TimeUnit.SECONDS);
            if (!locked) {
                redisTemplate.opsForList().rightPush("grading:pending", dto);
                System.out.println(("채점이 지연되었으며 큐에 추가됨: {}"+ lockKey));
                return -1;
            }

            List<Question> questions = questionService.getQuestionsFromCache(dto.getSubject());
            for (Question q : questions) {
                System.out.println("Question Number: " + q.getQuestionNumber());
                System.out.println("Sub Question Number: " + q.getSubQuestionNumber());
                System.out.println("Answer: " + q.getAnswer());
                System.out.println("Point: " + q.getPoint());
                System.out.println("Answer Count: " + q.getAnswerCount());
                System.out.println("Question Type: " + q.getQuestionType());
                System.out.println("-----");
            }

            return gradeWithAnswerChecking(dto, questions, student);

        } catch (Exception e) {
            throw new RuntimeException("채점 중 오류 발생: " + e.getMessage());
        } finally {
            if (locked && lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }





    @Transactional
    public void updateStudentResponses(StudentAnswerUpdateDto dto) {
        String subject = dto.getSubject();
        List<StudentAnswerUpdateDto.StudentAnswers> studentAnswersList = dto.getStudentAnswersList();

        for (StudentAnswerUpdateDto.StudentAnswers studentAnswers : studentAnswersList) {
            String studentId = studentAnswers.getStudent_id();

            Student student = studentService.findById(studentId)
                    .orElseThrow(() -> new RuntimeException("해당 학생을 찾을 수 없습니다. id: " + studentId));

            StudentResponse response = studentResponseRepository.findByStudentAndSubject(student, subject)
                    .orElseThrow(() -> new RuntimeException("해당 학생의 응답을 찾을 수 없습니다."));

            List<ExamResponse> answerList = response.getAnswers();
            if (answerList == null) continue;

            float totalScore = response.getTotalScore();

            for (StudentAnswerUpdateDto.StudentAnswers.AnswerDto answerDto : studentAnswers.getAnswers()) {
                int qNo = answerDto.getQuestion_number();
                int subQNo = answerDto.getSub_question_number();

                ExamResponse matchedAnswer = answerList.stream()
                        .filter(a -> a.getQuestionNumber() == qNo && a.getSubQuestionNumber() == subQNo)
                        .findFirst()
                        .orElse(null);

                if (matchedAnswer == null) {
                    System.out.printf("⚠️ 답변 없음: 학생 ID: %d, Q%d-%d\n", studentId, qNo, subQNo);
                    continue;
                }

                float previousScore = matchedAnswer.getScore();
                String newStudentAnswer = answerDto.getStudent_answer();
                matchedAnswer.setStudentAnswer(newStudentAnswer);

                // 문제 정보 조회
                Question question = questionService.findQuestionBySubjectAndNumber(subject, qNo, subQNo);
                if (question != null) {
                    String correctAnswer = question.getAnswer();

                    boolean isCorrect = newStudentAnswer != null && correctAnswer != null &&
                            newStudentAnswer.trim().replaceAll("\\s+", "")
                                    .equalsIgnoreCase(correctAnswer.trim().replaceAll("\\s+", ""));

                    float newScore = isCorrect ? question.getPoint() : 0;

                    matchedAnswer.setCorrect(isCorrect);
                    matchedAnswer.setScore(newScore);

                    totalScore += (newScore - previousScore);
                } else {
                    matchedAnswer.setCorrect(false);
                    matchedAnswer.setScore(0);
                    totalScore -= previousScore;
                }
            }

            // ✅ StudentResponse 저장 시 ExamResponse도 같이 저장됨
            response.setTotalScore(totalScore);
            studentResponseRepository.save(response);
        }
    }





}