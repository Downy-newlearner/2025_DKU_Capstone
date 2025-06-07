package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.LowConfidenceImageDto;

import com.checkmate.ai.entity.LowConfidenceImage;
import com.checkmate.ai.entity.Image; // 별도 엔티티 Image import

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public class LowConfidenceImageMapper {

    private static final Pattern QN_PATTERN = Pattern.compile("qn_(\\d+)");
    private static final Pattern AC_PATTERN = Pattern.compile("ac_(\\d+)");


    // Mapper 내 toEntity 수정
    public static LowConfidenceImage toEntity(LowConfidenceImageDto dto) {
        LowConfidenceImage entity = new LowConfidenceImage();
        entity.setSubject(dto.getSubject());

        List<Image> images = dto.getImages().stream()
                .map(dtoImage -> {
                    Image img = new Image();
                    img.setFileName(dtoImage.getFile_name());
                    img.setBase64Data(dtoImage.getBase64_data());
                    img.setStudentId(dtoImage.getStudent_id());

                    img.setQuestionNumber(dtoImage.getQuestion_number());
                    img.setSubQuestionNumber(dtoImage.getSub_question_number());

                    return img;
                })
                .collect(Collectors.toList());

        entity.setImages(images);

        return entity;
    }



    public static LowConfidenceImageDto toDto(LowConfidenceImage entity) {
        if (entity == null) return null;

        LowConfidenceImageDto dto = new LowConfidenceImageDto();
        dto.setSubject(entity.getSubject());
        dto.setImages(entity.getImages().stream()
                .map(imgEntity -> {
                    LowConfidenceImageDto.Image imgDto = new LowConfidenceImageDto.Image();
                    imgDto.setFile_name(imgEntity.getFileName());
                    imgDto.setBase64_data(imgEntity.getBase64Data());
                    imgDto.setStudent_id(imgEntity.getStudentId());
                    imgDto.setQuestion_number(imgEntity.getQuestionNumber());
                    imgDto.setSub_question_number(imgEntity.getSubQuestionNumber());
                    return imgDto;
                }).collect(Collectors.toList())
        );

        return dto;
    }
}
