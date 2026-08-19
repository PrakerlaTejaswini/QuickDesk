from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False)

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(20),
        nullable=False
    )

    tickets = relationship(
        "Ticket",
        back_populates="employee"
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=False
    )

    attachment_filename = Column(
        String(255),
        nullable=True
    )

    category = Column(
        String(50),
        nullable=False,
        default="Other"
    )

    priority = Column(
        String(50),
        nullable=False,
        default="Medium"
    )

    ai_category = Column(
        String(50),
        nullable=True
    )

    ai_priority = Column(
        String(50),
        nullable=True
    )

    ai_draft = Column(
        Text,
        nullable=True
    )

    final_reply = Column(
        Text,
        nullable=True
    )

    citations = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(30),
        nullable=False,
        default="Open"
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    resolved_at = Column(
        DateTime,
        nullable=True
    )

    employee = relationship(
        "User",
        back_populates="tickets"
    )

    audits = relationship(
        "OverrideAudit",
        back_populates="ticket",
        cascade="all, delete-orphan"
    )


class OverrideAudit(Base):
    __tablename__ = "override_audits"

    id = Column(
        Integer,
        primary_key=True
    )

    ticket_id = Column(
        Integer,
        ForeignKey("tickets.id"),
        nullable=False
    )

    agent_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    field = Column(
        String(50),
        nullable=False
    )

    old_value = Column(
        String(100),
        nullable=False
    )

    new_value = Column(
        String(100),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    ticket = relationship(
        "Ticket",
        back_populates="audits"
    )