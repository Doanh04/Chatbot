package com.chatbot.backend.DTO.response;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;

public record UserResponse(
        UUID id,
        String username,
        String email,
        String phone,
        String fullName,
        Instant createAt,
        Instant updateAt,
        Set<String> roles) {
}
