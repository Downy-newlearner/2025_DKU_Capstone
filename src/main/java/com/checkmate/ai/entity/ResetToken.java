package com.checkmate.ai.entity;

import lombok.Getter;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Document
@Getter
@Setter
public class ResetToken {

    @Id
    private String id; // MongoDB에서 자동 생성되는 ID
    private String email; // 비밀번호 재설정 요청을 한 이메일
    private String token; // 비밀번호 리셋을 위한 고유 토큰

}
