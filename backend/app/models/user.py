"""
User model for authentication and authorization.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Uuid as UUID
from sqlalchemy.orm import relationship
import enum

from app.db.base import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    EMPLOYEE = "employee"
    IT_STAFF = "it_staff"
    ADMIN = "admin"


class User(Base):
    """
    User model representing employees, IT staff, and admins.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        Enum(UserRole, name="user_role", native_enum=False),
        nullable=False,
        default=UserRole.EMPLOYEE
    )
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    # tickets_created = relationship("Ticket", foreign_keys="Ticket.requester_id", back_populates="requester")
    # tickets_assigned = relationship("Ticket", foreign_keys="Ticket.assignee_id", back_populates="assignee")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
