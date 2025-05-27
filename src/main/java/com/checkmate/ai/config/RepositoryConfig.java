// 파일: com/checkmate/ai/config/RepositoryConfig.java

package com.checkmate.ai.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.data.mongodb.repository.config.EnableMongoRepositories;

@Configuration
@EnableMongoRepositories(basePackages = "com.checkmate.ai.repository.mongo")
@EnableJpaRepositories(basePackages = "com.checkmate.ai.repository.jpa")
public class RepositoryConfig {
    // 필요 시 MongoTemplate, EntityManager 설정 가능
}
