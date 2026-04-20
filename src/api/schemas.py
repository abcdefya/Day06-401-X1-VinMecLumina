from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

LLMProvider = Literal["azure", "groq"]
MessageRole = Literal["system", "user", "assistant"]


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class AnalyzeRequest(BaseModel):
    patient_id: str | None = None
    initial_state: dict[str, Any] | None = None
    llm_provider: LLMProvider = "azure"
    create_conversation: bool = True


class AnalyzeResponse(BaseModel):
    result: dict[str, Any]
    conversation_id: str | None = None


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: str | None = None
    patient_id: str | None = None
    workflow_result: dict[str, Any] | None = None
    llm_provider: LLMProvider = "azure"


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str
    history: list[ChatMessage]


class ConversationSnapshot(BaseModel):
    conversation_id: str
    history: list[ChatMessage]


class ErrorResponse(BaseModel):
    detail: str
