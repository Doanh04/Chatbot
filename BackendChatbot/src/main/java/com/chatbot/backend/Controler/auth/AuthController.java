package com.chatbot.backend.Controler.auth;

import com.chatbot.backend.DTO.request.LoginRequest;
import com.chatbot.backend.DTO.request.RegisterRequest;
import com.chatbot.backend.DTO.response.ApiResponse;
import com.chatbot.backend.DTO.response.TokenResponse;
import com.chatbot.backend.DTO.response.UserResponse;
import com.chatbot.backend.DTO.response.VerifyTokenResponse;
import com.chatbot.backend.Service.auth.AuthService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.oauth2.jwt.Jwt;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;

    @PostMapping("/register")
    public ResponseEntity<ApiResponse<UserResponse>> register(@Valid @RequestBody RegisterRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.<UserResponse>builder().result(authService.register(request)).build());
    }

    @PostMapping("/login")
    public ApiResponse<TokenResponse> login(@Valid @RequestBody LoginRequest request) {
        return ApiResponse.<TokenResponse>builder().result(authService.login(request)).build();
    }

    @GetMapping("/verify")
    public ApiResponse<VerifyTokenResponse> verify() {
        return ApiResponse.<VerifyTokenResponse>builder()
                .result(new VerifyTokenResponse(true))
                .build();
    }

    @PostMapping("/logout")
    public ApiResponse<Void> logout(@AuthenticationPrincipal Jwt jwt) {
        authService.logout(jwt);
        return ApiResponse.<Void>builder().message("Logged out successfully.").build();
    }
}
