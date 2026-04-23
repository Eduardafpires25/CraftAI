from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=72, description="Senha deve ter entre 6 e 72 caracteres")

class UserResponse(BaseModel):
    id: int
    email: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72, description="Senha deve ter no máximo 72 caracteres")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
