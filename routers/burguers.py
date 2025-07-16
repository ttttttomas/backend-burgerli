from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from sqlalchemy import text
from Database.getConnection import engine
import uuid
import os
import shutil

router = APIRouter()

IMAGES_DIR = "/app/images"
DOMAIN_URL = "https://api-burgerli.iwebtecnology.com/images"

@router.post("/burgers", tags=["Food"])
async def create_burger(
    size: str = Form(...),
    description: str = Form(...),
    price: str = Form(...),
    stock: bool = Form(...),
    favorite: bool = Form(...),
    ingredients: str = Form(...)
):
    burger_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO burger (id_burger, size, description, price, stock, favorite, ingredients) "
                 "VALUES (:id, :size, :description, :price, :stock, :favorite, :ingredients)"),
            {"id": burger_id, "size": size, "description": description, "price": price,
             "stock": stock, "favorite": favorite, "ingredients": ingredients}
        )
    return {"message": "Burger creada", "id": burger_id}

@router.get("/burgers", tags=["Food"])
def get_burgers():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM burger")).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fries", tags=["Food"])
async def create_fries(
    name: str = Form(...),
    size: str = Form(...),
    price: float = Form(...),
    description: str = Form(...),
    stock: bool = Form(...),
    favourite: bool = Form(...)
):
    fries_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO fries (id_fries, name, size, price, description, stock, favourite) "
                 "VALUES (:id, :name, :size, :price, :description, :stock, :favourite)"),
            {"id": fries_id, "name": name, "size": size, "price": price,
             "description": description, "stock": stock, "favourite": favourite}
        )
    return {"message": "Fries creadas", "id": fries_id}

@router.get("/fries", tags=["Food"])
def get_fries():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM fries")).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drinks", tags=["Food"])
async def create_drinks(
    name: str = Form(...),
    size: str = Form(...),
    price: float = Form(...),
    stock: bool = Form(...),
    favourite: bool = Form(...)
):
    drink_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO drinks (id_drinks, name, size, price, stock, favourite) "
                 "VALUES (:id, :name, :size, :price, :stock, :favourite)"),
            {"id": drink_id, "name": name, "size": size, "price": price,
             "stock": stock, "favourite": favourite}
        )
    return {"message": "Drink creada", "id": drink_id}

@router.get("/drinks", tags=["Food"])
def get_drinks():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM drinks")).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combos", tags=["Combos & Promos"])
async def create_combo(
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    burgers: str = Form(...),  # IDs separados por coma
    fries: str = Form(...),
    drinks: str = Form(...)
):
    combo_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO combos (id_combos, name, quantity, price) VALUES (:id, :name, :quantity, :price)"),
            {"id": combo_id, "name": name, "quantity": quantity, "price": price}
        )

        for b in burgers.split(","):
            conn.execute(
                text("INSERT INTO combo_burger (id_combo_burger, id_combo, id_burger) VALUES (:id, :combo, :burger)"),
                {"id": str(uuid.uuid4()), "combo": combo_id, "burger": b.strip()}
            )

        for f in fries.split(","):
            conn.execute(
                text("INSERT INTO combo_fries (id_combo_fries, id_combo, id_fries) VALUES (:id, :combo, :fries)"),
                {"id": str(uuid.uuid4()), "combo": combo_id, "fries": f.strip()}
            )

        for d in drinks.split(","):
            conn.execute(
                text("INSERT INTO combo_drinks (id_combo_drinks, id_combo, id_drinks) VALUES (:id, :combo, :drinks)"),
                {"id": str(uuid.uuid4()), "combo": combo_id, "drinks": d.strip()}
            )

    return {"message": "Combo creado", "id": combo_id}

@router.get("/combos", tags=["Combos & Promos"])
def get_combos():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT c.*, cb.id_burger, cf.id_fries, cd.id_drinks
                FROM combos c
                LEFT JOIN combo_burger cb ON cb.id_combo = c.id_combos
                LEFT JOIN combo_fries cf ON cf.id_combo = c.id_combos
                LEFT JOIN combo_drinks cd ON cd.id_combo = c.id_combos
            """)).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/promos", tags=["Combos & Promos"])
async def create_promo(
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    burgers: str = Form(...),
    fries: str = Form(...),
    drinks: str = Form(...)
):
    promo_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO promos (id_promos, name, quantity, price) VALUES (:id, :name, :quantity, :price)"),
            {"id": promo_id, "name": name, "quantity": quantity, "price": price}
        )

        for b in burgers.split(","):
            conn.execute(
                text("INSERT INTO promo_burger (id_promo_burger, id_promo, id_burger) VALUES (:id, :promo, :burger)"),
                {"id": str(uuid.uuid4()), "promo": promo_id, "burger": b.strip()}
            )

        for f in fries.split(","):
            conn.execute(
                text("INSERT INTO promo_fries (id_promo_fries, id_promo, id_fries) VALUES (:id, :promo, :fries)"),
                {"id": str(uuid.uuid4()), "promo": promo_id, "fries": f.strip()}
            )

        for d in drinks.split(","):
            conn.execute(
                text("INSERT INTO promo_drinks (id_promo_drinks, id_promo, id_drinks) VALUES (:id, :promo, :drinks)"),
                {"id": str(uuid.uuid4()), "promo": promo_id, "drinks": d.strip()}
            )

    return {"message": "Promo creada", "id": promo_id}

@router.get("/promos", tags=["Combos & Promos"])
def get_promos():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT p.*, pb.id_burger, pf.id_fries, pd.id_drinks
                FROM promos p
                LEFT JOIN promo_burger pb ON pb.id_promo = p.id_promos
                LEFT JOIN promo_fries pf ON pf.id_promo = p.id_promos
                LEFT JOIN promo_drinks pd ON pd.id_promo = p.id_promos
            """)).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))