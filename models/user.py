from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserDB(Base):
    __tablename__ = "credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password = Column(String(100))
    rol = Column(String(50))
    local = Column(String(50))

class User(BaseModel):
    username: str
    password: str
    rol: str
    local: str
    
    class Config:
        from_attributes = True

class UserClient(Base):
    __tablename__ = "user_client"

    id_user_client = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    phone = Column(String(20))
    email = Column(String(100), unique=True, index=True)
    password = Column(String(100))
    locality = Column(String(100))
    notes = Column(String(255))