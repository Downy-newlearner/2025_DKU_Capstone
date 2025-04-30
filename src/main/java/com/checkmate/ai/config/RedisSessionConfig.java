package com.checkmate.ai.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession  // 스프링 세션을 Redis에 저장
public class RedisSessionConfig {
}

