package com.checkmate.ai.entity;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.util.List;

@Getter
@Setter
@Entity
public class LowConfidenceImage {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long lowConfidenceImageId;

    private String subject;

    @OneToMany(mappedBy = "lowConfidenceImage", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Image> images;

}