from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

class Order(BaseModel):
    id: str
    user_id: str
    message: str
    timestamp: datetime