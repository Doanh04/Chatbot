CREATE TABLE roles (
    id UUID PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    CONSTRAINT uk_roles_name UNIQUE (name)
);

CREATE TABLE users (
    id UUID PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(30),
    full_name VARCHAR(255),
    password_hash VARCHAR(255) NOT NULL,
    create_at TIMESTAMPTZ NOT NULL,
    update_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT uk_users_username UNIQUE (username),
    CONSTRAINT uk_users_email UNIQUE (email)
);

CREATE UNIQUE INDEX uk_users_username_ci ON users (lower(username));
CREATE UNIQUE INDEX uk_users_email_ci ON users (lower(email));

CREATE TABLE user_role (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id),
    CONSTRAINT uk_user_role UNIQUE (user_id, role_id)
);

CREATE INDEX ix_user_role_role_id ON user_role (role_id);

CREATE TABLE revoked_tokens (
    id UUID PRIMARY KEY,
    expires_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX ix_revoked_tokens_expires_at ON revoked_tokens (expires_at);

INSERT INTO roles (id, name) VALUES ('70bf379e-c207-41ad-b27e-45926216a439', 'USER');
