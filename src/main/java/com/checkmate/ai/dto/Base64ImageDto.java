package com.checkmate.ai.dto;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class Base64ImageDto {
    private String filename;
    private String base64Data;
}
