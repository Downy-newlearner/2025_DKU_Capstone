package com.checkmate.ai.entity;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.index.Indexed;

import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Document(collection = "Users")
@Getter
@Setter
@NoArgsConstructor
public class User{
    @Id
    private String objectId;


    private String email;

    private String password;

    private String name;

    @CreatedDate
    private LocalDateTime created_at;

    @LastModifiedDate
    private LocalDateTime update_at;


    public User(String email, String password, String name) {
        this.email = email;
        this.password = password;
        this.name= name;
    }
}