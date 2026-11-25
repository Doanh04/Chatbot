package com.chatbot.backend.exception;

import org.springframework.http.HttpStatus;

public enum ErrorCode {
    UNAUTHENTICATED(1005, "Authentication required or token is invalid.", HttpStatus.UNAUTHORIZED),
    ACCESS_DENIED(1006, "Access denied.", HttpStatus.FORBIDDEN),
    USER_EXISTS(1001, "Username or email already exists.", HttpStatus.CONFLICT),
    INVALID_CREDENTIALS(1002, "Invalid username/email or password.", HttpStatus.UNAUTHORIZED),
    INVALID_REQUEST(1004, "Dữ liệu yêu cầu không hợp lệ.", HttpStatus.BAD_REQUEST),
    UNKNOWN_ERROR(9999, "Hệ thống đang gặp lỗi. Vui lòng thử lại sau.", HttpStatus.INTERNAL_SERVER_ERROR);

    private final int code;
    private final String message;
    private final HttpStatus statusCode;

    ErrorCode(int code, String message, HttpStatus statusCode) {
        this.code = code;
        this.message = message;
        this.statusCode = statusCode;
    }

    public int getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    public HttpStatus getStatusCode() {
        return statusCode;
    }
}
