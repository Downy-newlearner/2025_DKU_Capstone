package com.checkmate.ai.mapper;

import com.checkmate.ai.dto.UserDto;
import com.checkmate.ai.entity.User;

public class UserMapper {

    public static UserDto toDto(User user) {
        return new UserDto(user.getEmail(), user.getName());
    }

    public static User toEntity(UserDto dto, String encodedPassword) {
        return new User(dto.getEmail(), encodedPassword, dto.getName());
    }
}
