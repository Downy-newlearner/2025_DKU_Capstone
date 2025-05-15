package com.checkmate.ai.entity;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;
import org.springframework.data.mongodb.core.mapping.Field;

import java.util.List;


@RequiredArgsConstructor
@Document
@Getter
@Setter
public class StudentResponse {
    @Id
    private String id;  // MongoDB에서 자동 생성되는 식별자 (ObjectId)
    private String studentId;  // 학생 ID
    private String subject;  // 시험 과목 이름
    private List<ExamResponse> answers;  // 학생의 응답 목록
    private int totalScore;




    // 생성자, getter, setter
}
