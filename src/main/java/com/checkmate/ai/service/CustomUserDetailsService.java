package com.checkmate.ai.service;

import com.checkmate.ai.dto.CustomUserDetails;
import com.checkmate.ai.entity.User;
import com.checkmate.ai.repository.mongo.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    @Override
    @Transactional
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        return userRepository.findByEmail(email)
                .map(this::createUserDetails)
                .orElseThrow(() -> new UsernameNotFoundException("해당 이메일을 가진 사용자를 찾을 수 없습니다."));
    }

    private UserDetails createUserDetails(User user) {
        return CustomUserDetails.builder()
                .email(user.getEmail())
                .objectId(user.getObjectId())
                .name(user.getName())
                .password(user.getPassword())
                .build();
    }
}
