"""
Ticket models for IT helpdesk ticketing system.
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Boolean, Enum, Index, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TicketCategory(str, enum.Enum):
    """Ticket category enumeration"""
    ACCOUNT = "account"
    DEVICE = "device"
    NETWORK = "network"
    SYSTEM = "system"
    SECURITY = "security"
    OTHER = "other"


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ON_HOLD = "on_hold"
    CLOSED = "closed"


class TicketPriority(str, enum.Enum):
    """Ticket priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Ticket(Base):
    """
    Ticket model for IT support requests.
    Created from unresolved chat sessions.
    """
    __tablename__ = "tickets"
    __table_args__ = (
        Index("ix_tickets_status", "status"),
        Index("ix_tickets_assignee_id", "assignee_id"),
        Index("ix_tickets_requester_id", "requester_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number = Column(Integer, unique=True, nullable=False, autoincrement=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(
        Enum(TicketCategory, name="ticket_category", native_enum=False),
        nullable=False
    )
    status = Column(
        Enum(TicketStatus, name="ticket_status", native_enum=False),
        nullable=False,
        default=TicketStatus.OPEN
    )
    priority = Column(
        Enum(TicketPriority, name="ticket_priority", native_enum=False),
        nullable=False,
        default=TicketPriority.MEDIUM
    )
    requester_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    assignee_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"), nullable=True, unique=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], backref="tickets_created")
    assignee = relationship("User", foreign_keys=[assignee_id], backref="tickets_assigned")
    session = relationship("ChatSession", back_populates="ticket", uselist=False)
    comments = relationship(
        "TicketComment",
        back_populates="ticket",
        order_by="TicketComment.created_at",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, ticket_number={self.ticket_number}, status={self.status})>"


class TicketComment(Base):
    """
    Comment/note on a ticket.
    Can be public (visible to requester) or internal (IT staff only).
    """
    __tablename__ = "ticket_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", backref="ticket_comments")

    def __repr__(self) -> str:
        return f"<TicketComment(id={self.id}, ticket_id={self.ticket_id}, is_internal={self.is_internal})>"
