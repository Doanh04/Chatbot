# ChatBot workspace

The root `compose.yaml` runs the Spring Boot backend, Python ChatBot API, and
one shared PostgreSQL database. BackendChatbot owns authentication and the
`users` table; ChatBot owns chat and knowledge tables.

```powershell
docker compose up --build -d
```

The existing root `.env` was moved from `ChatBot/.env`. If it is missing, copy
`.env.example` to `.env` and set `POSTGRES_PASSWORD` and
`AUTH_JWT_SECRET_BASE64` before starting. Backend health is available at
`http://localhost:8080/health`. PostgreSQL is exposed only on
`localhost:5432` for local development.

Apply the Python service's Alembic migrations after the backend has created
`users` with Flyway:

```powershell
docker compose run --rm app /app/.venv/bin/alembic upgrade head
```

## Local LLM

Install and start Ollama on the host, then check the installed model with
`ollama list`. Set `OLLAMA_MODEL` in the root `.env` to the exact model name
(for example, `qwen3-vi:latest`). Set `OLLAMA_BASE_URL` to
`http://host.docker.internal:11434` when Ollama runs on the host; the model
stays on the host. Compose uses these values when starting the Python container.

Use the configured client from Python code inside the ChatBot package:

```python
from chatbot.core.config import get_llm

response = await get_llm().ainvoke("Xin chào")
reply = response.content
```

The Python service listens on `http://localhost:8000`; `GET /health` checks
whether it is running. To test the model through HTTP:

```powershell
$body = @{ message = "Xin chào"; reasoning = $false } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/chat -Method Post -ContentType "application/json; charset=utf-8" -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

`reasoning` is optional and defaults to `false`. The response contains `reply`
and `model`.
