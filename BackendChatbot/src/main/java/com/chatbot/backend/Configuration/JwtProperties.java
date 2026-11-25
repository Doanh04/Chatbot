package com.chatbot.backend.Configuration;

import java.time.Duration;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "auth.jwt")
public record JwtProperties(String secretBase64, String issuer, Duration ttl) {

    public JwtProperties {
        if (ttl == null || ttl.isZero() || ttl.isNegative()) {
            throw new IllegalArgumentException("auth.jwt.ttl must be positive");
        }
    }
}
