from fastapi import FastAPI
from routers import login
from routers import testingWebSocket as ws
from routers.burguers import router as burger_router
from routers.orders import router as orders_router
from fastapi.middleware.cors import CORSMiddleware
import os
from routers.paymentController import router as payment_router
from fastapi.staticfiles import StaticFiles

app = FastAPI(root_path="/api")


origins = [
    "http://localhost:3000",
    "https://burgerli-website.vercel.app",
    "https://imido-curliest-cole.ngrok-free.dev",
    "https://cart-test-nu.vercel.app",
    "http://localhost:5500",
    "https://facudemarco.github.io",
    "https://api-burgerli.iwebtecnology.com",
]

app.add_middleware( 
    CORSMiddleware,
    allow_origins= origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Set-Cookie"],
)

IMAGES_DIR = os.path.join(os.getcwd(), "images")
app.mount("/api/images", StaticFiles(directory=IMAGES_DIR), name="images")

IS_PROD = os.getenv("ENV") == "production"
print(IS_PROD)

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(login.router)
app.include_router(ws.router)
app.include_router(burger_router)
app.include_router(payment_router)
app.include_router(orders_router)
