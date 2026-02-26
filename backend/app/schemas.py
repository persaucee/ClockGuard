from pydantic import BaseModel, EmailStr, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Generic, TypeVar, Optional

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

class EmployeeBase(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeCreate(EmployeeBase):
    pass
class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    email: Optional[EmailStr] = None

class EmployeeResponse(EmployeeBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)