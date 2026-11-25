"""Entry point for the local chatbot API."""

import uvicorn


def main() -> None:
    uvicorn.run("chatbot.api.app:app", host="0.0.0.0", port=8000)
