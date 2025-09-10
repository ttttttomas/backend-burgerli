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
DOMAIN_URL = "http://api-burgerli.iwebtecnology.com/api/images"

@router.post("/burgers", tags=["Food"])
async def create_burger(
    price: str = Form(...),
    stock: bool = Form(...),
    name: str = Form(...),
    main_image: UploadFile = File(..., description="Main image"),
    size: List[str] = Form(default=[]),
    description: str = Form(...),
    ingredients: List[str] = Form(default=[]),      
):
    burger_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO burger (id_burger, name, price, stock, description)
                VALUES (:id, :name, :price, :stock, :description)
            """),
            {
                "id": burger_id,
                "name": name,
                "price": price,
                "stock": stock,
                "description": description
            },
        )

    # Insert size
    normalized_size = []
    for d in size:
        if isinstance(d, str) and "," in d:
            normalized_size.extend([item.strip() for item in d.split(",") if item.strip()])
        elif d:
            normalized_size.append(d.strip())
    
    for d in normalized_size:
        if not d:
            continue
        conn.execute(
            text("""
                INSERT INTO burger_size (id, burger_id, size)
                VALUES (:id, :burger_id, :size)
            """),
            {"id": str(uuid.uuid4()), "burger_id": burger_id, "size": d}
        )
    
    # Insert ingredients
    normalized_ingredients = []
    for d in ingredients:
        if isinstance(d, str) and "," in d:
            normalized_ingredients.extend([item.strip() for item in d.split(",") if item.strip()])
        elif d:
            normalized_ingredients.append(d.strip())
    for d in normalized_ingredients:
        if not d:
            continue
        conn.execute(
            text("""
                INSERT INTO burger_ingredients (id, burger_id, ingredients)
                VALUES (:id, :burger_id, :ingredients)
            """),
            {"id": str(uuid.uuid4()), "burger_id": burger_id, "ingredients": d}
        )

    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)
    ext = os.path.splitext(main_image.filename or "file.jpg")[1]
    fname = f"{uuid.uuid4()}{ext}"
    path = os.path.join(IMAGES_DIR, fname)
    with open(path, "wb") as buf:
        shutil.copyfileobj(main_image.file, buf)
    url_main = f"{DOMAIN_URL}/{fname}"
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO burger_main_imgs (id, burger_id, url) VALUES (:id, :burger_id, :url)"),
            {"id": str(uuid.uuid4()), "burger_id": burger_id, "url": url_main}
        )
    return {"message": "Burger created", "id": burger_id, "main_image_url": url_main}

@router.get("/burgers", tags=["Food"])
def get_burgers():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM burger"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No burger found.")
            burgers = []
            for burger in rows:
                hid = burger["id_burger"]
                main = conn.execute(
                    text("SELECT url FROM burger_main_imgs WHERE burger_id = :id"),
                    {"id": hid}
                ).fetchone()

                size_list = conn.execute(
                    text("SELECT size FROM burger_size WHERE burger_id = :id"),
                    {"id": hid}
                ).scalars().all()

                description_list = conn.execute(
                    text("SELECT description FROM burger_description WHERE burger_id = :id"),
                    {"id": hid}
                ).scalars().all()

                ingredients_list = conn.execute(
                    text("SELECT ingredients FROM burger_ingredients WHERE burger_id = :id"),
                    {"id": hid}
                ).scalars().all()

                data = dict(burger)
                data["main_image"] = main[0] if main else None
                data["size_list"] = size_list
                data["description_list"] = description_list
                data["ingredients_list"] = ingredients_list
                burgers.append(data)
            return burgers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fries", tags=["Food"])
async def create_fries(
    name: str = Form(...),
    size: List[str] = Form(default=[]),
    description: List[str] = Form(default=[]),
    price: str = Form(...),
    stock: bool = Form(...),
    main_image: UploadFile = File(..., description="Main image")
):
    fries_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO fries (id_fries, name, price, stock)
                VALUES (:id, :name, :price, :stock)
            """),
            {
                "id": fries_id,
                "name": name,
                "price": price,
                "stock": stock,
            },
        )
    
    # Insert size
    normalized_size = []
    for d in size:
        if isinstance(d, str) and "," in d:
            normalized_size.extend([item.strip() for item in d.split(",") if item.strip()])
        elif d:
            normalized_size.append(d.strip())
    for d in normalized_size:
        if not d:
            continue
        conn.execute(
            text("""
                INSERT INTO fries_size (id, fries_id, size)
                VALUES (:id, :fries_id, :size)
            """),
            {"id": str(uuid.uuid4()), "fries_id": fries_id, "size": d}
        )
    
    # Insert description
    normalized_description = []
    for d in description:
        if isinstance(d, str) and "," in d:
            normalized_description.extend([item.strip() for item in d.split(",") if item.strip()])
        elif d:
            normalized_description.append(d.strip())
    for d in normalized_description:
        if not d:
            continue
        conn.execute(
            text("""
                INSERT INTO fries_description (id, fries_id, description)
                VALUES (:id, :fries_id, :description)
            """),
            {"id": str(uuid.uuid4()), "fries_id": fries_id, "description": d}
        )

    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)
    ext = os.path.splitext(main_image.filename or "file.jpg")[1]
    fname = f"{uuid.uuid4()}{ext}"
    path = os.path.join(IMAGES_DIR, fname)
    with open(path, "wb") as buf:
        shutil.copyfileobj(main_image.file, buf)
    url_main = f"{DOMAIN_URL}/{fname}"
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO fries_main_imgs (id, fries_id, url) VALUES (:id, :fries_id, :url)"),
            {"id": str(uuid.uuid4()), "fries_id": fries_id, "url": url_main}
        )
    return {"message": "Fries created", "id": fries_id, "main_image_url": url_main}

@router.get("/fries", tags=["Food"])
def get_fries():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM fries"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No fries found.")
            fries = []
            for fries in rows:
                hid = fries["id_fries"]
                main = conn.execute(
                    text("SELECT url FROM fries_main_imgs WHERE fries_id = :id"),
                    {"id": hid}
                ).fetchone()

                size_list = conn.execute(
                    text("SELECT size FROM fries_size WHERE fries_id = :id"),
                    {"id": hid}
                ).scalars().all()

                description_list = conn.execute(
                    text("SELECT description FROM fries_description WHERE fries_id = :id"),
                    {"id": hid}
                ).scalars().all()

                data = dict(fries)
                data["main_image"] = main[0] if main else None
                data["size_list"] = size_list
                data["description_list"] = description_list
                fries.append(data)
            return fries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/drinks", tags=["Food"])
async def create_drinks(
    name: str = Form(...),
    price: str = Form(...),
    stock: bool = Form(...),
    size: List[str] = Form(default=[]),
    main_image: UploadFile = File(..., description="Main image")
):
    drinks_id = str(uuid.uuid4())
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO drinks (id_drinks, name, size, price, stock)
                VALUES (:id, :name, :size, :price, :stock)
            """),
            {
                "id": drinks_id,
                "name": name,
                "price": price,
                "stock": stock,
            },
        )
    
    # Insert size
    normalized_size = []
    for d in size:
        if isinstance(d, str) and "," in d:
            normalized_size.extend([item.strip() for item in d.split(",") if item.strip()])
        elif d:
            normalized_size.append(d.strip())
    for d in normalized_size:
        if not d:
            continue
        conn.execute(
            text("""
                INSERT INTO drinks_size (id, drinks_id, size)
                VALUES (:id, :drinks_id, :size)
            """),
            {"id": str(uuid.uuid4()), "drinks_id": drinks_id, "size": d}
        )

    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR, exist_ok=True)
    ext = os.path.splitext(main_image.filename or "file.jpg")[1]
    fname = f"{uuid.uuid4()}{ext}"
    path = os.path.join(IMAGES_DIR, fname)
    with open(path, "wb") as buf:
        shutil.copyfileobj(main_image.file, buf)
    url_main = f"{DOMAIN_URL}/{fname}"
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO drinks_main_imgs (id, drinks_id, url) VALUES (:id, :drinks_id, :url)"),
            {"id": str(uuid.uuid4()), "drinks_id": drinks_id, "url": url_main}
        )
    return {"message": "Drinks created", "id": drinks_id, "main_image_url": url_main}

@router.get("/drinks", tags=["Food"])
def get_drinks():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM drinks"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No drinks found.")
            drinks = []
            for drinks in rows:
                hid = drinks["id_drinks"]
                main = conn.execute(
                    text("SELECT url FROM drinks_main_imgs WHERE drinks_id = :id"),
                    {"id": hid}
                ).fetchone()

                size_list = conn.execute(
                    text("SELECT size FROM drinks_size WHERE drinks_id = :id"),
                    {"id": hid}
                ).scalars().all()

                data = dict(drinks)
                data["main_image"] = main[0] if main else None
                data["size_list"] = size_list
                drinks.append(data)
            return drinks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/combos", tags=["Combos & Promos"])
async def create_combo(
    name: str = Form(...),
    quantity: int = Form(...),
    price: float = Form(...),
    burgers: str = Form(...),
    fries: str = Form(...),
    drinks: str = Form(...)
):
    combo_id = str(uuid.uuid4())

    def _split_csv(value: str):
        return [x.strip() for x in value.split(",") if x.strip()]

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO combos (id_combos, name, quantity, price)
                VALUES (:id, :name, :quantity, :price)
            """),
            {"id": combo_id, "name": name, "quantity": quantity, "price": price},
        )

        for b in _split_csv(burgers):
            conn.execute(
                text("""
                    INSERT INTO combo_burger (id_combo_burger, id_combo, id_burger)
                    VALUES (:id, :combo, :burger)
                """),
                {"id": str(uuid.uuid4()), "combo": combo_id, "burger": b},
            )

        for f in _split_csv(fries):
            conn.execute(
                text("""
                    INSERT INTO combo_fries (id_combo_fries, id_combo, id_fries)
                    VALUES (:id, :combo, :fries)
                """),
                {"id": str(uuid.uuid4()), "combo": combo_id, "fries": f},
            )

        for d in _split_csv(drinks):
            conn.execute(
                text("""
                    INSERT INTO combo_drinks (id_combo_drinks, id_combo, id_drinks)
                    VALUES (:id, :combo, :drinks)
                """),
                {"id": str(uuid.uuid4()), "combo": combo_id, "drinks": d},
            )

    return {"message": "Combo created", "id": combo_id}

@router.get("/combos", tags=["Combos & Promos"])
def get_combos():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT c.*, cb.id_burger, cf.id_fries, cd.id_drinks
                    FROM combos c
                    LEFT JOIN combo_burger cb ON cb.id_combo = c.id_combos
                    LEFT JOIN combo_fries cf ON cf.id_combo = c.id_combos
                    LEFT JOIN combo_drinks cd ON cd.id_combo = c.id_combos
                """)
            ).mappings().all()
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

    def _split_csv(value: str):
        return [x.strip() for x in value.split(",") if x.strip()]

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO promos (id_promos, name, quantity, price)
                VALUES (:id, :name, :quantity, :price)
            """),
            {"id": promo_id, "name": name, "quantity": quantity, "price": price},
        )

        for b in _split_csv(burgers):
            conn.execute(
                text("""
                    INSERT INTO promo_burger (id_promo_burger, id_promo, id_burger)
                    VALUES (:id, :promo, :burger)
                """),
                {"id": str(uuid.uuid4()), "promo": promo_id, "burger": b},
            )

        for f in _split_csv(fries):
            conn.execute(
                text("""
                    INSERT INTO promo_fries (id_promo_fries, id_promo, id_fries)
                    VALUES (:id, :promo, :fries)
                """),
                {"id": str(uuid.uuid4()), "promo": promo_id, "fries": f},
            )

        for d in _split_csv(drinks):
            conn.execute(
                text("""
                    INSERT INTO promo_drinks (id_promo_drinks, id_promo, id_drinks)
                    VALUES (:id, :promo, :drinks)
                """),
                {"id": str(uuid.uuid4()), "promo": promo_id, "drinks": d},
            )

    return {"message": "Promo created", "id": promo_id}

@router.get("/promos", tags=["Combos & Promos"])
def get_promos():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT p.*, pb.id_burger, pf.id_fries, pd.id_drinks
                    FROM promos p
                    LEFT JOIN promo_burger pb ON pb.id_promo = p.id_promos
                    LEFT JOIN promo_fries pf ON pf.id_promo = p.id_promos
                    LEFT JOIN promo_drinks pd ON pd.id_promo = p.id_promos
                """)
            ).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_users", tags=["Users"])
def get_users():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id_user_client, name
                    FROM user_client
                """)
            ).mappings().all()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_users/{id_user_client}", tags=["Users"])
def get_user_with_favorites(id_user_client: str):
    try:
        with engine.connect() as conn:
            user = conn.execute(
                text("""
                    SELECT id_user_client, name, email, phone, password, locality, direction, notes
                    FROM user_client
                    WHERE id_user_client = :id_user_client
                """),
                {"id_user_client": id_user_client},
            ).mappings().first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            favorites = conn.execute(
                text("""
                    SELECT f.favourite_id, f.status, fp.product_type, fp.product_id
                    FROM favourites f
                    LEFT JOIN favourites_products fp ON f.favourite_id = fp.favourite_id
                    WHERE f.user_id = :id_user_client
                """),
                {"id_user_client": id_user_client},
            ).mappings().all()

        fav_map = {}
        for fav in favorites:
            fid = fav["favourite_id"]
            if fid not in fav_map:
                fav_map[fid] = {"favourite_id": fid, "status": fav["status"], "products": []}
            if fav["product_id"]:
                fav_map[fid]["products"].append(
                    {"type": fav["product_type"], "id": fav["product_id"]}
                )

        return {**user, "favorites": list(fav_map.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create_user", tags=["Users"])
def create_user(user: UserCreate):
    try:
        user_id = str(uuid.uuid4())
        payload = user.model_dump()
        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO user_client (id_user_client, name, email, phone, password, locality, direction, notes)
                    VALUES (:id_user_client, :name, :email, :phone, :password, :locality, :direction, :notes)
                """),
                {**payload, "id_user_client": user_id},
            )
        return {"message": "User created successfully", "id_user_client": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mod-user/{id_user_client}", tags=["Users"])
def update_user(id_user_client: str, user: UserUpdate):
    try:
        payload = user.model_dump()
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    UPDATE user_client
                    SET name = :name,
                        email = :email,
                        phone = :phone,
                        password = :password,
                        locality = :locality,
                        direction = :direction,
                        notes = :notes
                    WHERE id_user_client = :id_user_client
                """),
                {**payload, "id_user_client": id_user_client},
            )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User updated successfully", "id_user_client": id_user_client}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_user/{id_user_client}", tags=["Users"])
def delete_user(id_user_client: str):
    try:
        with engine.begin() as conn:
            result = conn.execute(
                text("""
                    DELETE FROM user_client
                    WHERE id_user_client = :id_user_client
                """),
                {"id_user_client": id_user_client},
            )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")

        return {"message": "User deleted successfully", "id_user_client": id_user_client}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{id_user_client}/favourites", tags=["Users"])
def create_favourite(id_user_client: str, favourite: FavouriteCreate):
    try:
        with engine.begin() as conn:
            user = conn.execute(
                text("""
                    SELECT id_user_client
                    FROM user_client
                    WHERE id_user_client = :id_user_client
                """),
                {"id_user_client": id_user_client},
            ).first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            favourite_id = str(uuid.uuid4())

            conn.execute(
                text("""
                    INSERT INTO favourites (favourite_id, user_id, status)
                    VALUES (:favourite_id, :user_id, :status)
                """),
                {"favourite_id": favourite_id, "user_id": id_user_client, "status": favourite.status},
            )

            for product in favourite.products:
                conn.execute(
                    text("""
                        INSERT INTO favourites_products (favourite_id, product_type, product_id)
                        VALUES (:favourite_id, :product_type, :product_id)
                    """),
                    {
                        "favourite_id": favourite_id,
                        "product_type": product.product_type,
                        "product_id": product.product_id,
                    },
                )

        return {"message": "Favorite created successfully", "favourite_id": favourite_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/users/{id_user_client}/favourites/toggle", tags=["Users"])
def toggle_favourite(
    id_user_client: str,
    payload: FavouriteToggleRequest = Body(...)
):
    try:
        with engine.begin() as conn:
            user = conn.execute(
                text("""
                    SELECT id_user_client
                    FROM user_client
                    WHERE id_user_client = :id
                """),
                {"id": id_user_client},
            ).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            fav = conn.execute(
                text("""
                    SELECT favourite_id, status
                    FROM favourites
                    WHERE user_id = :uid
                    ORDER BY favourite_id ASC
                    LIMIT 1
                """),
                {"uid": id_user_client},
            ).mappings().first()

            if not fav:
                favourite_id = str(uuid.uuid4())
                conn.execute(
                    text("""
                        INSERT INTO favourites (favourite_id, user_id, status)
                        VALUES (:fid, :uid, :status)
                    """),
                    {"fid": favourite_id, "uid": id_user_client, "status": "active"},
                )
            else:
                favourite_id = fav["favourite_id"]

            existing = conn.execute(
                text("""
                    SELECT 1
                    FROM favourites_products
                    WHERE favourite_id = :fid
                      AND product_type = :ptype
                      AND product_id = :pid
                    LIMIT 1
                """),
                {
                    "fid": favourite_id,
                    "ptype": payload.product_type,
                    "pid": payload.product_id,
                },
            ).first()

            if existing:
                conn.execute(
                    text("""
                        DELETE FROM favourites_products
                        WHERE favourite_id = :fid
                          AND product_type = :ptype
                          AND product_id = :pid
                    """),
                    {
                        "fid": favourite_id,
                        "ptype": payload.product_type,
                        "pid": payload.product_id,
                    },
                )
                return {
                    "message": "Removed from favorites",
                    "favourite_id": favourite_id,
                    "favorited": False,
                    "product": payload.model_dump(),
                }
            else:
                conn.execute(
                    text("""
                        INSERT INTO favourites_products (favourite_id, product_type, product_id)
                        VALUES (:fid, :ptype, :pid)
                    """),
                    {
                        "fid": favourite_id,
                        "ptype": payload.product_type,
                        "pid": payload.product_id,
                    },
                )
                return {
                    "message": "Added to favorites",
                    "favourite_id": favourite_id,
                    "favorited": True,
                    "product": payload.model_dump(),
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/get_orders", tags=["Default"])
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