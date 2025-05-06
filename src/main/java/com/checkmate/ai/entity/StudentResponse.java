package com.checkmate.ai.entity;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.RequiredArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.List;


@RequiredArgsConstructor
@Document
@Getter
@Setter
public class StudentResponse {
    @Id
    private String id;  // MongoDB에서 자동 생성되는 식별자 (ObjectId)
    private String student_id;  // 학생 ID
    private String subject;  // 시험 과목 이름
    private List<ExamResponse> answers;  // 학생의 응답 목록
    private int total_score;




    // 생성자, getter, setter
}
