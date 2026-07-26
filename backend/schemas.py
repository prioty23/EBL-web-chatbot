from typing import Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    source: str
    blocked: bool = False
    quick_actions: list[str] = Field(default_factory=list)
    chat_id: Optional[int] = None


class ChatFeedbackRequest(BaseModel):
    chat_id: int
    session_id: Optional[str] = None
    feedback: str


class ComplaintStatusUpdateRequest(BaseModel):
    status: str
