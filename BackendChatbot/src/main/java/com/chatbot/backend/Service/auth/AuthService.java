package com.chatbot.backend.Service.auth;

import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Locale;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

import com.chatbot.backend.Constain.RoleName;
import com.chatbot.backend.Configuration.JwtProperties;
import com.chatbot.backend.DTO.request.LoginRequest;
import com.chatbot.backend.DTO.request.RegisterRequest;
import com.chatbot.backend.DTO.response.TokenResponse;
import com.chatbot.backend.DTO.response.UserResponse;
import com.chatbot.backend.Repository.RevokedTokenRepository;
import com.chatbot.backend.Repository.RoleRepository;
import com.chatbot.backend.Repository.UserRepository;
import com.chatbot.backend.entity.RevokedToken;
import com.chatbot.backend.entity.Role;
import com.chatbot.backend.entity.User;
import com.chatbot.backend.exception.AppException;
import com.chatbot.backend.exception.ErrorCode;
import com.chatbot.backend.mapper.UserMapper;
import org.springframework.dao.DataIntegrityViolationException;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.jose.jws.MacAlgorithm;
import org.springframework.security.oauth2.jwt.JwsHeader;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.security.oauth2.jwt.JwtClaimsSet;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.JwtEncoderParameters;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final RoleRepository roleRepository;
    private final RevokedTokenRepository revokedTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtEncoder jwtEncoder;
    private final JwtProperties jwtProperties;
    private final UserMapper userMapper;

    @Transactional
    public UserResponse register(RegisterRequest request) {
        if (request.password().getBytes(StandardCharsets.UTF_8).length > 72) {
            throw new AppException(ErrorCode.INVALID_REQUEST);
        }
        String email = request.email().trim().toLowerCase(Locale.ROOT);
        if (userRepository.existsByUsernameIgnoreCase(request.username())
                || userRepository.existsByEmailIgnoreCase(email)) {
            throw new AppException(ErrorCode.USER_EXISTS);
        }
        Role userRole = roleRepository.findByName(RoleName.USER)
                .orElseThrow(() -> new IllegalStateException("USER role is missing"));
        User user = userMapper.toEntity(request);
        user.setEmail(email);
        user.setPasswordHash(passwordEncoder.encode(request.password()));
        user.getRoles().add(userRole);
        try {
            return userMapper.toResponse(userRepository.saveAndFlush(user));
        } catch (DataIntegrityViolationException exception) {
            throw new AppException(ErrorCode.USER_EXISTS);
        }
    }

    @Transactional(readOnly = true)
    public TokenResponse login(LoginRequest request) {
        String identifier = request.usernameOrEmail().trim();
        User user = (identifier.contains("@")
                ? userRepository.findByEmailIgnoreCase(identifier)
                : userRepository.findByUsernameIgnoreCase(identifier))
                .orElseThrow(() -> new AppException(ErrorCode.INVALID_CREDENTIALS));
        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new AppException(ErrorCode.INVALID_CREDENTIALS);
        }
        Instant issuedAt = Instant.now();
        Instant expiresAt = issuedAt.plus(jwtProperties.ttl());
        Set<String> roles = user.getRoles().stream().map(role -> role.getName().name())
                .collect(Collectors.toSet());
        JwtClaimsSet claims = JwtClaimsSet.builder()
                .issuer(jwtProperties.issuer())
                .subject(user.getId().toString())
                .id(UUID.randomUUID().toString())
                .issuedAt(issuedAt)
                .expiresAt(expiresAt)
                .claim("roles", roles)
                .build();
        String token = jwtEncoder.encode(JwtEncoderParameters.from(
                JwsHeader.with(MacAlgorithm.HS256).build(), claims)).getTokenValue();
        return new TokenResponse(token, "Bearer", expiresAt);
    }

    @Transactional
    public void logout(Jwt jwt) {
        revokedTokenRepository.save(new RevokedToken(UUID.fromString(jwt.getId()), jwt.getExpiresAt()));
    }

}
