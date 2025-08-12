from typing import Optional, Literal, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

class UserCreate(BaseModel):
    id_user_client: str
    name: str
    email: str
    phone: str
    password: str
    locality: str
    direction: str
    notes: Optional[str] = None

class UserUpdate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    locality: str
    direction: str
    notes: Optional[str] = None

class FavouriteProduct(BaseModel):
    product_type: Literal['burger', 'fries', 'drinks', 'combo', 'promo', 'dayPromo']
    product_id: str

class FavouriteCreate(BaseModel):
    status: bool
    products: List[FavouriteProduct]

class FavouriteToggleRequest(BaseModel):
    product_type: str  # e.g. "burger" | "fries" | "drinks" | "combo" | "promo"
    product_id: str