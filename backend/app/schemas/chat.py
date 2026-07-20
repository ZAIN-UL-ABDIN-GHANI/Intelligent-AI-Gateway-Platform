"""Request/response schemas for chat completions."""
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    messages: list[ChatMessage]
    model: str = "auto"
    stream: bool = False
    session_id: Optional[str] = None
    force_backend: Optional[str] = None

    @field_validator("messages")
    @classmethod
    def messages_non_empty(cls, v):
        if not v or all(not m.content.strip() for m in v):
            raise ValueError("messages must contain at least one non-empty message")
        return v


class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cost: float


class ChatCompletionResponse(BaseModel):
    id: str
    trace_id: str
    routed_model: str
    content: str
    usage: Usage
    cache_hit: bool = False


class FeedbackRequest(BaseModel):
    trace_id: str
    rating: str = Field(pattern="^(up|down)$")
    comment: Optional[str] = None
