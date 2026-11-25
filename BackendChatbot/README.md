# BackendChatbot

Spring Boot 4.1 / Java 21 authentication backend. It owns the `users`, `roles`,
`user_role`, and `revoked_tokens` tables in the shared PostgreSQL database.

Source packages under `com.chatbot.backend`: `Configuration`, `Constain`,
`Controler`, `DTO`, `entity`, `exception`, `mapper`, `Repository`, and `Service`.
`BackendChatbotApplication` remains in the root package for component scanning.
Auth and health controllers live in `Controler/auth` and `Controler/health`;
auth services live in `Service/auth`. DTOs are grouped under `DTO/request` and
`DTO/response`. `mapper/UserMapper` uses MapStruct for request/entity/response
mapping; password hashing and default-role assignment stay in the auth service.

The auth model maps `users` and `roles` with UUID primary keys and a `user_role`
join table. Users have a username, email, phone, full name, password hash, and
creation/update timestamps. `users.id` matches the foreign key expected by ChatBot.
Flyway creates the auth tables and seeds `USER` and `ADMIN` roles on startup.

All API responses use `{ "code": 1000, "result": ... }` on success and
`{ "code": errorCode, "message": "..." }` on errors; null fields are omitted.
Business code can
throw `new AppException(ErrorCode.INVALID_REQUEST)`; add specific error codes
to `ErrorCode` when a feature needs them.

## Run locally

Requires Java 21, Maven 3.6.3+, and PostgreSQL. The root `.env` supplies
`POSTGRES_PASSWORD` and `AUTH_JWT_SECRET_BASE64`. If it is missing, copy
`.env.example` from the root and set both values. Generate a signing key with:

```powershell
$bytes = New-Object byte[] 32
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
[Convert]::ToBase64String($bytes)
```

Put the output in `.env` as `AUTH_JWT_SECRET_BASE64=...`. Keep it private and
stable; changing it invalidates all existing tokens.

Then run:

```powershell
docker compose up -d postgres-db
cd BackendChatbot
mvn spring-boot:run
```

Open `http://localhost:8080/health`. Spring Boot loads `.env` from the parent
directory. Root `compose.yaml` exposes PostgreSQL to localhost on port 5432.

## Run with Docker

Maven is not needed on the host when building with Docker. After setting the
password in the root `.env`, run from the root directory:

```powershell
docker compose up -d postgres-db backend
```

The Compose project name stays `chatbot` to preserve the existing database
volume and network names.

ChatBot owns its chat and knowledge tables, which reference `users.id`. Both
services point to the same PostgreSQL database and manage only their own tables.

## Auth API

- `POST /auth/register`: JSON `username`, `email`, `password`, optional `phone`
  and `fullName`. Returns `201` with the user profile in `result`. Passwords are BCrypt-hashed.
- `POST /auth/login`: JSON `usernameOrEmail`, `password`. Returns a signed
  `accessToken`, `tokenType: Bearer`, and `expiresAt` inside `result`.
- `GET /auth/verify`: `Authorization: Bearer <accessToken>`. Validates the
  signature, expiry, issuer, revocation status, and user. Returns
  `{ "code": 1000, "result": { "valid": true } }`; invalid tokens receive `401`.
- `POST /auth/logout`: same header. Revokes this access token and returns `200`.
  Subsequent requests with it receive `401`.

The access token lives for one hour by default (`AUTH_JWT_TTL`, ISO-8601
duration). Roles are included in the signed token as `roles` and mapped to
Spring Security `ROLE_` authorities. Registration always assigns `USER`; the
client cannot choose roles. Method-level role checks can use `@PreAuthorize`.
The `ADMIN` role is seeded without creating an admin account; role names use
the `Constain/RoleName` enum and are stored as strings in PostgreSQL.
The server stores only revoked token IDs, not raw
tokens. Expired revocation rows can be removed periodically.
