package com.checkmate.ai.service;

import com.checkmate.ai.dto.QuestionDto;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.repository.QuestionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class QuestionService {

    @Autowired
    private QuestionRepository questionRepository;

}
