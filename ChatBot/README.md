# Chatbot database models

## Calling the local LLM

`chatbot.core.config` reads the Ollama model and base URL from the environment
and provides a reusable LangChain `ChatOllama` client. Import it from any
Python module in this package:

```python
from chatbot.core.config import get_llm

response = await get_llm().ainvoke("Xin chào")
reply = response.content

# Enable thinking for a specific call:
response_with_thinking = await get_llm(reasoning=True).ainvoke("Giải bài toán này")
```

`get_llm()` defaults to `reasoning=False` and caches a client for each mode.
`ainvoke()` sends the message to
Ollama and returns an `AIMessage`; read its `content` for the reply. Ollama
settings are independent of database settings, so creating the LLM client does
not require a database password. The Python API exposes `GET /health` and
`POST /chat` for testing; send `{"message": "Xin chào", "reasoning": false}`.
With the current custom `qwen3-vi:latest` model, `content` can still include
`<think>...</think>` even when `reasoning=False`; callers that need only the
final answer must handle that output.

Models live in `src/chatbot/core/db/models/chatbot.py`:

- `knowledge_folders`, `knowledge_files`
- `chat_sessions`, `chat_messages`
- `session_folders`, `session_files` (many-to-many links)

All IDs and `user_id` references use PostgreSQL UUID. The backend must create
`users` with a UUID primary key named `id` in the same database (and visible
through the connection's search path) before chatbot tables are created.

The `users` Table in metadata is only a reference for foreign keys, not the full
backend schema. Do not migrate or create it from the chatbot application.

## Knowledge folder repository

`KnowledgeFolderRepository` receives an `AsyncSession`. Every read, update, and
delete requires the owner's `user_id`:

```python
from chatbot.core.repositories import KnowledgeFolderRepository

repo = KnowledgeFolderRepository(db_session)
folder = await repo.create(user_id=user_id, name="Tài liệu", description=None)
await repo.update(
    folder_id=folder.id,
    user_id=user_id,
    changes={"description": "Tài liệu của tôi"},
)
await db_session.commit()
```

Use `get_by_id`, `list_by_user`, and `delete` for the other operations. Repository
methods flush changes but leave commit or rollback to the caller. Pass
`{"description": None}` to clear a description. Deleting a folder also removes
its files because the model defines a delete-orphan relationship.

## Knowledge file repository

`KnowledgeFileRepository` also receives an `AsyncSession`. Its CRUD methods
require `user_id`, and `list_by_folder_id` returns only that user's files in the
specified folder:

```python
from chatbot.core.repositories import KnowledgeFileRepository

repo = KnowledgeFileRepository(db_session)
file = await repo.create(
    user_id=user_id,
    folder_id=folder_id,
    name="notes.pdf",
    storage_key="uploads/notes.pdf",
    storage_backend="local",
)
files = await repo.list_by_folder_id(folder_id=folder_id, user_id=user_id)
await db_session.commit()
```

Use `get_by_id`, `list_by_user`, `update`, and `delete` for the other operations.
`update` accepts a `changes` mapping; `{"folder_id": None}` removes a file from
its folder, while `{"metadata": {...}}` updates its JSON metadata. Creating or
moving a file into a folder requires that folder to belong to the same user.
Deleting a record does not remove the physical file from its storage backend.
The caller controls commit or rollback.

## Alembic migrations

The backend creates `users` with Flyway. Start it first and wait for
`http://localhost:8080/health` to return OK. Then apply ChatBot migrations:

```powershell
docker compose build app
docker compose run --rm app /app/.venv/bin/alembic upgrade head
docker compose run --rm app /app/.venv/bin/alembic current
```

Run these commands from the workspace root. The initial revision creates six
ChatBot tables. Alembic records its version in `chatbot_alembic_version`, separate
from Flyway's history table. Migrations are explicit; starting the API does not
modify the database schema.

When models change, generate and review a new revision:

```powershell
cd ChatBot
uv run alembic revision --autogenerate --rev-id 002 -m "chatdoc"
cd ..
docker compose build app
docker compose run --rm app /app/.venv/bin/alembic upgrade head
docker compose run --rm app /app/.venv/bin/alembic check
```

On Windows where local Python execution is blocked, generate the revision from
Docker while mounting the migrations directory:

```powershell
docker compose run --rm -v "${PWD}/ChatBot/migrations:/app/migrations" app /app/.venv/bin/alembic revision --autogenerate --rev-id 002 -m "chatdoc"
```

`migrations/env.py` includes only ChatBot-owned tables during schema comparison;
the reference to `users` is excluded. Review every generated revision before
applying it. For development-only `create_all`, `chatbot.core.db.session.init_db()`
also excludes `users`; use Alembic for normal schema changes.

Revision IDs are sequential three-digit numbers. Use the next unused number
with `--rev-id` and a short functional name with `-m`; for example,
`002_chatdoc.py` or `003_add_file_metadata.py`. Keep each new revision's
`down_revision` pointing to the previous revision.
