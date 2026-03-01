from datetime import datetime
from typing import Generic, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

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

#Employee Schemas

class EmployeeBase(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeCreate(EmployeeBase):
    embedding: list[float] = Field(min_length=512, max_length=512)
    pass
class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeResponse(EmployeeBase):
    id: UUID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class VerifyRequest(BaseModel):
    embedding: list[float] = Field(min_length=512, max_length=512)