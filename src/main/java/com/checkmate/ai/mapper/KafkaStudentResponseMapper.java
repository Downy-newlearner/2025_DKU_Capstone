package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.KafkaStudentResponseDto;
import org.springframework.stereotype.Component;

import java.util.List;

@Component
public class KafkaStudentResponseMapper {
    // KafkaStudentResponseDto.ExamResponseDto를 KafkaStudentResponseDto로 변환
    public KafkaStudentResponseDto toDto(KafkaStudentResponseDto.ExamResponseDto answer) {
        KafkaStudentResponseDto dto = new KafkaStudentResponseDto();
        // 여기에서 적절하게 KafkaStudentResponseDto의 필드를 설정하는 로직을 추가
        // 예시로, DTO의 `answers`에 `answer`를 추가하는 부분을 구현
        dto.setAnswers(List.of(answer));
        // 나머지 필드들 설정 (예: studentId, subject 등)
        return dto;
    }
}
