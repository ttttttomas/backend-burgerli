from typing import List, Optional
from fastapi import APIRouter, HTTPException, Form, Body, UploadFile, File
import os
import shutil
from sqlalchemy import text
from Database.getConnection import engine
import uuid
from models.users_client import UserCreate, UserUpdate, FavouriteCreate, FavouriteToggleRequest

router = APIRouter()

IMAGES_DIR = "images/"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/api/images"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")


@router.get("/get_orders", tags=["Orders"])
def get_orders():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM orders
                     """)
            ).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/orders", tags=["Orders"])
async def create_order(
    payment_method: str = Form(...),
    delivery_mode: str = Form(...),
    price: float = Form(...),
    status: str = Form(...),
    order_notes: Optional[str] = Form(None),
    local: str = Form(...),
    burgerst: List[str] = Form(default=[]),
    burgers: str = Form(...),
    friest: List[str] = Form(default=[]),
    fries: str = Form(...),
    drinkst: List[str] = Form(default=[]),
    drinks: str = Form(...),
    user_client_id: str = Form(...),
    sint: List[str] = Form(default=[]),
    sin: str = Form(...),
    extrat: List[str] = Form(default=[]),
    extra: str = Form(...),
    combot: List[str] = Form(default=[]),
    combo: str = Form(...),
    promost: List[str] = Form(default=[]),
    promos: str = Form(...)
):
    try:
        order_id = str(uuid.uuid4())
        
        with engine.begin() as conn:
            # Create new order
            conn.execute(
                text("""
                    INSERT INTO orders (
                        id_order, payment_method, delivery_mode, price, 
                        status, order_notes, local, burgers, fries,
                        drinks, user_client_id, sin, extra, combo, promos
                    ) VALUES (
                        :id_order, :payment_method, :delivery_mode, :price,
                        :status, :order_notes, :local, :burgers, :fries,
                        :drinks, :user_client_id, :sin, :extra, :combo, :promos
                    )
                """),
                {
                    "id_order": order_id,
                    "payment_method": payment_method,
                    "delivery_mode": delivery_mode,
                    "price": price,
                    "status": status,
                    "order_notes": order_notes,
                    "local": local,
                    "burgers": burgers,
                    "fries": fries,
                    "drinks": drinks,
                    "user_client_id": user_client_id,
                    "sin": sin,
                    "extra": extra,
                    "combo": combo,
                    "promos": promos
                }
            )

        return {
            "message": "Order created successfully",
            "order_id": order_id,
            "status": status
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
