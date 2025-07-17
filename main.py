from fastapi import FastAPI
from routers import login
from routers import testingWebSocket as ws
from routers.burguers import router as burger_router
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# origins = [
#     "http://localhost:3000",
#     "https://cart-test-nu.vercel.app",
#     "http://127.0.0.1:5500",
#     "localhost:5500",
#     "http://localhost:5500",
#     "https://facudemarco.github.io",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://test-car-sage.vercel.app"],
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