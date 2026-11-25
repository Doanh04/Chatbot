"""HTTP endpoints for testing the ChatBot service."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from chatbot.core.config import get_llm


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    reasoning: bool = False


class ChatResponse(BaseModel):
    reply: str
    model: str

app = FastAPI(title="ChatBot")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    llm = get_llm(reasoning=request.reasoning)
    try:
        response = await llm.ainvoke(request.message)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

    reply = response.content
    if not isinstance(reply, str):
        raise HTTPException(status_code=502, detail="Ollama returned invalid content")
    if "</think>" in reply:
        reply = reply.rsplit("</think>", 1)[1]
    reply = reply.strip()
    if not reply or reply.startswith("<think>"):
        raise HTTPException(status_code=502, detail="Ollama returned no final answer")
    return ChatResponse(reply=reply, model=llm.model)
