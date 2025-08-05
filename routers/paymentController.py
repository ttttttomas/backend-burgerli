from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

@router.post("/mercadopago/create-order")
async def create_mp_order(order_data: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3000/create-order",
                json=order_data
            )
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))