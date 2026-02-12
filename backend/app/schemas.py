from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

class APIResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None

class LoginData(BaseModel):
    username: str
    password: str
    
class UserData(BaseModel):
    username: str
    full_name: Optional[str] = None

