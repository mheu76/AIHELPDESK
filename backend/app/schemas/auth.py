"""
Pydantic schemas for authentication endpoints.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator, computed_field
from typing import Optional
from datetime import datetime
import uuid

from app.models.user import UserRole


class LoginRequest(BaseModel):
    """Login request schema"""
    employee_id: Optional[str] = Field(None, min_length=3, max_length=20, description="Employee ID")
    email: Optional[EmailStr] = Field(None, description="User email address")
    password: str = Field(..., min_length=8, description="User password")

    @model_validator(mode="after")
    def validate_identifier(self):
        if not self.employee_id and not self.email:
            raise ValueError("Either employee_id or email is required")
        return self


class RegisterRequest(BaseModel):
    """User registration request schema"""
    employee_id: str = Field(..., min_length=3, max_length=20, description="Employee ID")
    email: EmailStr = Field(..., description="Email address")
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full name")
    password: str = Field(..., min_length=8, description="Password")
    department: Optional[str] = Field(None, max_length=100, description="Department")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        # Add more validation if needed (uppercase, numbers, special chars)
        return v

    @model_validator(mode="after")
    def normalize_name(self):
        self.name = self.name or self.full_name
        self.full_name = self.full_name or self.name
        if not self.name:
            raise ValueError("name or full_name is required")
        return self


class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: Optional["UserResponse"] = Field(default=None, description="Authenticated user")


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token")


class UserResponse(BaseModel):
    """User response schema"""
    id: uuid.UUID
    employee_id: str
    email: str
    name: str
    role: UserRole
    department: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def full_name(self) -> str:
        return self.name

    model_config = {
        "from_attributes": True
    }


class ChangePasswordRequest(BaseModel):
    """Change password request schema"""
    current_password: str = Field(..., min_length=8, description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str, info) -> str:
        """Validate new password is different from current"""
        if "current_password" in info.data and v == info.data["current_password"]:
            raise ValueError("New password must be different from current password")
        return v
