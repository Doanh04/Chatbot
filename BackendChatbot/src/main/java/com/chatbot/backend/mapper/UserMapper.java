package com.chatbot.backend.mapper;

import com.chatbot.backend.DTO.request.RegisterRequest;
import com.chatbot.backend.DTO.response.UserResponse;
import com.chatbot.backend.entity.Role;
import com.chatbot.backend.entity.User;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.ReportingPolicy;

@Mapper(componentModel = "spring", unmappedTargetPolicy = ReportingPolicy.ERROR)
public interface UserMapper {

    @Mapping(target = "id", ignore = true)
    @Mapping(target = "email", ignore = true)
    @Mapping(target = "passwordHash", ignore = true)
    @Mapping(target = "createAt", ignore = true)
    @Mapping(target = "updateAt", ignore = true)
    @Mapping(target = "roles", ignore = true)
    User toEntity(RegisterRequest request);

    UserResponse toResponse(User user);

    default String roleName(Role role) {
        return role.getName().name();
    }
}
