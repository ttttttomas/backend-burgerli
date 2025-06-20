from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user
from routers import login

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

app.include_router(login.router)