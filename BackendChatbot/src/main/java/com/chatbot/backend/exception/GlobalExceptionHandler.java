package com.chatbot.backend.exception;

import com.chatbot.backend.DTO.response.ApiResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.web.ErrorResponse;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(AppException.class)
    public ResponseEntity<ApiResponse<Void>> handleAppException(AppException exception) {
        ErrorCode errorCode = exception.getErrorCode();
        return response(errorCode, errorCode.getStatusCode());
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleException(Exception exception) {
        if (exception instanceof ErrorResponse errorResponse && errorResponse.getStatusCode().is4xxClientError()) {
            return response(ErrorCode.INVALID_REQUEST, errorResponse.getStatusCode());
        }

        log.error("Unhandled request error", exception);
        return response(ErrorCode.UNKNOWN_ERROR, ErrorCode.UNKNOWN_ERROR.getStatusCode());
    }

    private ResponseEntity<ApiResponse<Void>> response(ErrorCode errorCode, HttpStatusCode statusCode) {
        return ResponseEntity.status(statusCode)
                .body(ApiResponse.<Void>builder()
                        .code(errorCode.getCode())
                        .message(errorCode.getMessage())
                        .build());
    }
}
