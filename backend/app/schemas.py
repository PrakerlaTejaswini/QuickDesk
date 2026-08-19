from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class TicketCreate(BaseModel):
    title: str
    description: str
    attachment_filename: Optional[str] = None


class TicketReply(BaseModel):
    reply: str


class TicketOverride(BaseModel):
    category: Optional[str] = None
    priority: Optional[str] = None