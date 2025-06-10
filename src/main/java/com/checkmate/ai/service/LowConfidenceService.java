package com.checkmate.ai.service;

import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.Image;
import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.mapper.LowConfidenceImageMapper;
import com.checkmate.ai.repository.jpa.ExamRepository;
import com.checkmate.ai.repository.jpa.LowConfidenceImageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class LowConfidenceService {



    @Autowired
    LowConfidenceImageRepository lowConfidenceImageRepository;

    @Autowired
    ExamRepository examRepository;

    public boolean saveImages(LowConfidenceImageDto dto) {
        LowConfidenceImage images = LowConfidenceImageMapper.toEntity(dto);
        lowConfidenceImageRepository.save(images);
        return true;
    }


    public Optional<LowConfidenceImageDto> getLowConfidenceImages(String subject) {
        Optional<LowConfidenceImage> lowConfidenceImageOptional = lowConfidenceImageRepository.findBySubject(subject);
        Optional<Exam> examOptional = examRepository.findBySubject(subject);  // subject로 Exam 조회

        if (lowConfidenceImageOptional.isEmpty() || examOptional.isEmpty()) {
            return Optional.empty();
        }

        LowConfidenceImage entity = lowConfidenceImageOptional.get();
        Exam exam = examOptional.get();

        List<LowConfidenceImageDto.Image> imageList = entity.getImages().stream()
                .map(img -> new LowConfidenceImageDto.Image(
                        img.getStudentId(),
                        img.getFileName(),
                        img.getBase64Data(),
                        img.getQuestionNumber(),
                        img.getSubQuestionNumber()
                ))
                .collect(Collectors.toList());

        LowConfidenceImageDto dto = new LowConfidenceImageDto(
                subject,
                exam.getExamDate(),  // Exam 엔티티의 examDate 가져오기
                imageList
        );

        return Optional.of(dto);
    }




}
