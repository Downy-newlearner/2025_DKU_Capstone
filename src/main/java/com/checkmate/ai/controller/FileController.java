package com.checkmate.ai.controller;

import com.checkmate.ai.dto.Base64ImageDto;
import com.checkmate.ai.service.FileService;
import com.checkmate.ai.service.ImageService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/images")
public class FileController {

    @Autowired
    private FileService fileService;

    @GetMapping("/{subject}/low-confidence-images")
    public List<Base64ImageDto> getBase64Images(@PathVariable("subject") String subject) {
        return fileService.getLowConfidenceImages(subject);
    }
}
