package com.checkmate.ai.entity;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.util.List;

@Getter
@Setter
@Document(collection = "low_confidence_images")
public class LowConfidenceImage {

    @Id
    private String id;
    private String subject;
    private List<Image> images;


    @Getter
    @Setter
    @NoArgsConstructor
    public static class Image {
        private String filename;
        private String base64Data;
        private String studentId;
        private int questionNumber;
        private int subQuestionNumber;

    }
}
