// com.checkmate.ai.dto.PasswordChangeRequest.java
package com.checkmate.ai.dto;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
public class PasswordChangeRequest {
    private String current_password;
    private String new_password;
    private String token;
}


