from fastapi import FastAPI
from routers import login
from routers import testingWebSocket as ws
from routers.burguers import router as burger_router
from fastapi.middleware.cors import CORSMiddleware
import os
from routers.paymentController import router as payment_router

app = FastAPI(root_path="/api")

origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://cart-test-nu.vercel.app",
    "http://127.0.0.1:5500",
    "localhost:5500",
    "http://localhost:5500",
    "https://facudemarco.github.io",
    "https://api-burgerli.iwebtecnology.com",
]

app.add_middleware( 
    CORSMiddleware,
    allow_origins=[origins[0], origins[1], origins[2], origins[3], origins[4], origins[5], origins[6]],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

IS_PROD = os.getenv("ENV") == "production"
print(IS_PROD)

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(login.router)
app.include_router(ws.router)
app.include_router(burger_router)
app.include_router(payment_router)