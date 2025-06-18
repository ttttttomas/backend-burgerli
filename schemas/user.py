from pydantic import BaseModel

class UserCreate(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    email: str
    password: str