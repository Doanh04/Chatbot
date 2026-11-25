package com.chatbot.backend.Repository;

import java.util.Optional;
import java.util.UUID;

import com.chatbot.backend.Constain.RoleName;
import com.chatbot.backend.entity.Role;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RoleRepository extends JpaRepository<Role, UUID> {

    Optional<Role> findByName(RoleName name);
}
