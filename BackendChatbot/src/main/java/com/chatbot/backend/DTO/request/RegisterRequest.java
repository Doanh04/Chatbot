package com.chatbot.backend.DTO.request;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank @Pattern(regexp = "[A-Za-z0-9_.-]{3,100}") String username,
        @NotBlank @Email @Size(max = 255) String email,
        @Size(max = 30) String phone,
        @Size(max = 255) String fullName,
        @NotBlank @Size(min = 8, max = 72) String password) {
}
