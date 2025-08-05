from fastapi import APIRouter, HTTPException
import httpx
from pydantic import BaseModel

router = APIRouter()

class OrderData(BaseModel):
    title: str
    description: str
    quantity: int
    unit_price: float
    picture_url: str | None = None
    category_id: str | None = None
    currency_id: str = "ARS"
    id: str | None = None

class Item(BaseModel):
    items: list[OrderData]

@router.post("/mercadopago/create-order")
async def create_mp_order(order_data: Item):
    print(order_data)
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://mercadopago-micro-service:3000/create-order",
                json=order_data.dict()
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))