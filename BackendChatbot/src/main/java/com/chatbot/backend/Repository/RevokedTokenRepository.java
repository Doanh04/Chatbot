package com.chatbot.backend.Repository;

import java.util.UUID;

import com.chatbot.backend.entity.RevokedToken;
import org.springframework.data.jpa.repository.JpaRepository;

public interface RevokedTokenRepository extends JpaRepository<RevokedToken, UUID> {
}
