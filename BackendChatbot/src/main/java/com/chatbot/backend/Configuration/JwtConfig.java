package com.chatbot.backend.Configuration;

import java.util.Base64;
import java.util.UUID;

import javax.crypto.SecretKey;
import javax.crypto.spec.SecretKeySpec;

import com.chatbot.backend.Repository.RevokedTokenRepository;
import com.chatbot.backend.Repository.UserRepository;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.BadJwtException;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtDecoder;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtValidators;
import org.springframework.security.oauth2.jwt.NimbusJwtDecoder;
import org.springframework.security.oauth2.jwt.NimbusJwtEncoder;

@Configuration
@EnableConfigurationProperties(JwtProperties.class)
public class JwtConfig {

    @Bean
    SecretKey jwtSecretKey(JwtProperties jwtProperties) {
        byte[] secret;
        try {
            secret = Base64.getDecoder().decode(jwtProperties.secretBase64());
        } catch (IllegalArgumentException exception) {
            throw new IllegalStateException("AUTH_JWT_SECRET_BASE64 must be valid Base64", exception);
        }
        if (secret.length < 32) {
            throw new IllegalStateException("AUTH_JWT_SECRET_BASE64 must contain at least 32 random bytes");
        }
        return new SecretKeySpec(secret, "HmacSHA256");
    }

    @Bean
    JwtEncoder jwtEncoder(SecretKey jwtSecretKey) {
        return NimbusJwtEncoder.withSecretKey(jwtSecretKey).algorithm(MacAlgorithm.HS256).build();
    }

    @Bean
    JwtDecoder jwtDecoder(
            SecretKey jwtSecretKey,
            JwtProperties jwtProperties,
            RevokedTokenRepository revokedTokenRepository,
            UserRepository userRepository) {
        NimbusJwtDecoder decoder = NimbusJwtDecoder.withSecretKey(jwtSecretKey)
                .macAlgorithm(MacAlgorithm.HS256)
                .build();
        decoder.setJwtValidator(JwtValidators.createDefaultWithIssuer(jwtProperties.issuer()));
        return token -> {
            Jwt jwt = decoder.decode(token);
            if (jwt.getId() == null || jwt.getSubject() == null) {
                throw new BadJwtException("Token has invalid claims");
            }
            try {
                UUID tokenId = UUID.fromString(jwt.getId());
                UUID userId = UUID.fromString(jwt.getSubject());
                if (revokedTokenRepository.existsById(tokenId) || !userRepository.existsById(userId)) {
                    throw new BadJwtException("Token is no longer valid");
                }
            } catch (IllegalArgumentException exception) {
                throw new BadJwtException("Token has invalid claims", exception);
            }
            return jwt;
        };
    }
}
