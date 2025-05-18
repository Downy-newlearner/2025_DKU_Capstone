package com.checkmate.ai.service;

import com.checkmate.ai.dto.LowConfidenceImageDto;
import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.mapper.LowConfidenceImageMapper;
import com.checkmate.ai.repository.LowConfidenceImageRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import java.util.Optional;

@Service
public class LowConfidenceService {



    @Autowired
    LowConfidenceImageRepository lowConfidenceImageRepository;


    public boolean saveImages(LowConfidenceImageDto dto) {
        LowConfidenceImage images = LowConfidenceImageMapper.toEntity(dto);
        lowConfidenceImageRepository.save(images);
        return true;
    }


    public Optional<LowConfidenceImage> getLowConfidenceImages(String subject) {
        return lowConfidenceImageRepository.findBySubject(subject);
    }



}
