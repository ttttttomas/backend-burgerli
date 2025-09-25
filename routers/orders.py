from typing import List, Optional
from fastapi import APIRouter, HTTPException, Form, Body, UploadFile, File
import os
import shutil
from sqlalchemy import text
from Database.getConnection import engine
import uuid
from models.users_client import UserCreate, UserUpdate, FavouriteCreate, FavouriteToggleRequest
from models.order import Order, OrderBurger, OrderDrinks, OrderFries, OrderExtra, OrderSin, OrderCoupons, OrderUserClient

router = APIRouter()

IMAGES_DIR = "images/"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/api/images"

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGES_DIR = os.path.join(PROJECT_ROOT, "images")

