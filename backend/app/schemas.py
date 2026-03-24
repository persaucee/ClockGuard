from datetime import datetime, time
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

T = TypeVar("T")

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None

class LoginData(BaseModel):
    username: str
    password: str
    
class UserData(BaseModel):
    username: str
    first_name: str
    last_name: str
    company: Optional[str] = None
    organization_id: UUID

#Employee Schemas

class EmployeeBase(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeCreate(EmployeeBase):
    embedding: list[float] = Field(min_length=512, max_length=512)

class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeResponse(EmployeeBase):
    id: UUID
    organization_id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class VerifyRequest(BaseModel):
    embedding: list[float] = Field(min_length=512, max_length=512)
    action: Optional[str] = "IN"
    
class OrganizationBase(BaseModel):
    default_open_time: Optional[time] = None
    default_close_time: Optional[time] = None
    @field_validator("default_open_time", "default_close_time", mode="before")
    @classmethod
    def enforce_hhmm(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            if len(v) != 5 or v[2] != ":":
                raise ValueError("Time must be in HH:MM format")
            v = time.fromisoformat(v)
        if v.second != 0 or v.microsecond != 0:
            raise ValueError("Time must be in HH:MM format with no seconds")
        return v
    
class OrganizationRequest(OrganizationBase):
    pass

class OrganizationResponse(OrganizationBase):
    pass

class AttendanceRecordBase(BaseModel):
    id: UUID
    employee_name: str
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    total_hours: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class AttendanceRecordResponse(AttendanceRecordBase):
    pass


# 2FA Schemas

class LoginResponseData(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[UUID] = None
    two_factor_required: bool = False
    temp_token: Optional[str] = None


class Verify2FARequest(BaseModel):
    temp_token: str
    code: str


class TwoFactorSetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class TwoFactorCodeRequest(BaseModel):
    code: str