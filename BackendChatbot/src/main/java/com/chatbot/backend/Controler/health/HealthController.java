package com.chatbot.backend.Controler.health;

import java.util.Map;

import com.chatbot.backend.DTO.response.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HealthController {

    @GetMapping("/health")
    public ApiResponse<Map<String, String>> health() {
        return ApiResponse.<Map<String, String>>builder().result(Map.of("status", "ok")).build();
    }
}
