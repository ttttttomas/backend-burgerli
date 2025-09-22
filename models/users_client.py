from typing import Optional, Literal, List
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Form

class UserCreate(BaseModel):
    id_user_client: str 
    name: str = Form(...)
    email: str = Form(...)
    phone: str = Form(...)
    password: str = Form(...)
    locality: str = Form(...)
    address: Optional[List[str]] = Form(default=[])
    notes: Optional[str] = Form(...)

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