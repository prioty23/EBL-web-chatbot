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


class LiveChatStartRequest(BaseModel):
    session_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None


class LiveChatAcceptRequest(BaseModel):
    agent_id: Optional[str] = None


class LiveChatMessageRequest(BaseModel):
    sender_type: str
    message: str
    sender_id: Optional[str] = None


class LiveChatEndRequest(BaseModel):
    ended_by: Optional[str] = None


class LiveChatFeedbackRequest(BaseModel):
    feedback: str


class AgentLoginRequest(BaseModel):
    email: str
    password: str
