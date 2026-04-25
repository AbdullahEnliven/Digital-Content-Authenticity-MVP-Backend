from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    organization: str | None = None
    job_role: str | None = None
    bio: str | None = None
    daily_credit_limit: int = 250
    credits_remaining: int = 250
    credits_reset_date: date | None = None


class TokenResponse(BaseModel):
    access_token: str
    user: UserOut


class UserUpdate(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    organization: str | None = None
    job_role: str | None = None
    bio: str | None = None


class UserStats(BaseModel):
    total_verifications: int
    verified_authentic: int
    ai_detected: int
    certificates_issued: int
