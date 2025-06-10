package com.checkmate.ai.entity;


import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;


@Getter
@Setter
@NoArgsConstructor
@Entity
public class Image {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long imageId;

    private String fileName;

    @Lob
    @Column(name = "base64_data", columnDefinition = "LONGTEXT")
    private String base64Data;
    private String studentId;
    private int questionNumber;
    private int subQuestionNumber;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "low_confidence_image_id")
    private LowConfidenceImage lowConfidenceImage;
}