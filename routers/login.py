from queue import PriorityQueue
import re
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from auth.authentication import oauth2_scheme, get_current_user, create_access_token
from models.user import User
from Database.users import verify_user_credentials, get_user_by_username, create_user, delete_user, get_user_by_id, get_user_by_username_and_password, update_user
from Database.getConnection import engine
from sqlalchemy import JSON, text
import uuid
import os
from fastapi.middleware.cors import CORSMiddleware
from models.users_client import UserCreate, UserUpdate, FavouriteCreate, FavouriteToggleRequest

IS_LOCAL = os.getenv("ENV") == "dev"

router = APIRouter()

# Users clients

@router.get("/get_users", tags=["Users Clients"])
def get_users():
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT * FROM user_client
                """))
            
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No users found")
            users = []
            for user in rows:
                hid = user["id_user_client"]
                address_list = conn.execute(
                    text("SELECT address FROM user_client_address WHERE user_id = :hid"),
                    {"hid": hid}
                ).scalars().all()

                data = dict(user)
                data["addresses"] = address_list
                users.append(data)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_users/{id_user_client}", tags=["Users Clients"])
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

@router.post("/create_user", tags=["Users Clients"])
def create_user(user: UserCreate):
    try:
        user_id = str(uuid.uuid4())
        payload = user.model_dump()

        normalized_addresses = payload.pop("address", [])

        with engine.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO user_client (id_user_client, name, email, phone, password, locality, notes)
                    VALUES (:id_user_client, :name, :email, :phone, :password, :locality, :notes)
                """),
                {**payload, "id_user_client": user_id},
            )

            for address in normalized_addresses:
                conn.execute(
                    text("""
                        INSERT INTO user_client_address (address_id, user_id, address)
                        VALUES (:address_id, :user_id, :address)
                    """),
                    {
                        "address_id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "address": address,
                    },
                )
        return {"message": "User created successfully", "id_user_client": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/mod-user/{id_user_client}", tags=["Users Clients"])
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

@router.delete("/delete_user/{id_user_client}", tags=["Users Clients"])
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

# @router.post("/users/{id_user_client}/favourites", tags=["Users Clients"])
# def create_favourite(id_user_client: str, favourite: FavouriteCreate):
#     try:
#         with engine.begin() as conn:
#             user = conn.execute(
#                 text("""
#                     SELECT id_user_client
#                     FROM user_client
#                     WHERE id_user_client = :id_user_client
#                 """),
#                 {"id_user_client": id_user_client},
#             ).first()

#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found")

#             favourite_id = str(uuid.uuid4())

#             conn.execute(
#                 text("""
#                     INSERT INTO favourites (favourite_id, user_id, status)
#                     VALUES (:favourite_id, :user_id, :status)
#                 """),
#                 {"favourite_id": favourite_id, "user_id": id_user_client, "status": favourite.status},
#             )

#             for product in favourite.products:
#                 conn.execute(
#                     text("""
#                         INSERT INTO favourites_products (favourite_id, product_type, product_id)
#                         VALUES (:favourite_id, :product_type, :product_id)
#                     """),
#                     {
#                         "favourite_id": favourite_id,
#                         "product_type": product.product_type,
#                         "product_id": product.product_id,
#                     },
#                 )

#         return {"message": "Favorite created successfully", "favourite_id": favourite_id}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

# @router.post("/users/{id_user_client}/favourites/toggle", tags=["Users"])
# def toggle_favourite(
#     id_user_client: str,
#     payload: FavouriteToggleRequest = Body(...)
# ):
#     try:
#         with engine.begin() as conn:
#             user = conn.execute(
#                 text("""
#                     SELECT id_user_client
#                     FROM user_client
#                     WHERE id_user_client = :id
#                 """),
#                 {"id": id_user_client},
#             ).first()
#             if not user:
#                 raise HTTPException(status_code=404, detail="User not found")

#             fav = conn.execute(
#                 text("""
#                     SELECT favourite_id, status
#                     FROM favourites
#                     WHERE user_id = :uid
#                     ORDER BY favourite_id ASC
#                     LIMIT 1
#                 """),
#                 {"uid": id_user_client},
#             ).mappings().first()

#             if not fav:
#                 favourite_id = str(uuid.uuid4())
#                 conn.execute(
#                     text("""
#                         INSERT INTO favourites (favourite_id, user_id, status)
#                         VALUES (:fid, :uid, :status)
#                     """),
#                     {"fid": favourite_id, "uid": id_user_client, "status": "active"},
#                 )
#             else:
#                 favourite_id = fav["favourite_id"]

#             existing = conn.execute(
#                 text("""
#                     SELECT 1
#                     FROM favourites_products
#                     WHERE favourite_id = :fid
#                       AND product_type = :ptype
#                       AND product_id = :pid
#                     LIMIT 1
#                 """),
#                 {
#                     "fid": favourite_id,
#                     "ptype": payload.product_type,
#                     "pid": payload.product_id,
#                 },
#             ).first()

#             if existing:
#                 conn.execute(
#                     text("""
#                         DELETE FROM favourites_products
#                         WHERE favourite_id = :fid
#                           AND product_type = :ptype
#                           AND product_id = :pid
#                     """),
#                     {
#                         "fid": favourite_id,
#                         "ptype": payload.product_type,
#                         "pid": payload.product_id,
#                     },
#                 )
#                 return {
#                     "message": "Removed from favorites",
#                     "favourite_id": favourite_id,
#                     "favorited": False,
#                     "product": payload.model_dump(),
#                 }
#             else:
#                 conn.execute(
#                     text("""
#                         INSERT INTO favourites_products (favourite_id, product_type, product_id)
#                         VALUES (:fid, :ptype, :pid)
#                     """),
#                     {
#                         "fid": favourite_id,
#                         "ptype": payload.product_type,
#                         "pid": payload.product_id,
#                     },
#                 )
#                 return {
#                     "message": "Added to favorites",
#                     "favourite_id": favourite_id,
#                     "favorited": True,
#                     "product": payload.model_dump(),
#                 }

#     except HTTPException:
#         raise
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
    

# Owners and employeeds

@router.post("/register", tags=["Login & Register"])
async def register(user: User):
    existing_user = get_user_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Username already registered"
        )
    success = create_user(user.username, user.password)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error creating user"
        )
    return {"message": "User created successfully"}

@router.post("/token", tags=["Login & Register"])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    if verify_user_credentials(form_data.username, form_data.password):
        user = get_user_by_username_and_password(
            username=form_data.username,
            password=form_data.password
        )
        if user is None:
            raise HTTPException(
                status_code=400,
                detail="User not found after verification"
            )
        access_token = create_access_token(
            data={"sub": form_data.username}
        )
        response = JSONResponse(
            content={"message": "Login successful, session stored in cookie.", "Token": access_token, "ID": user.id},
        )
        response.set_cookie(
            key="Authorization",
            value=access_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=3600,
            # domain="localhost" if IS_LOCAL else "api-burgerli.iwebtecnology.com",  # <--- CORREGIDO
            path="/",
        )
        return response

@router.get("/verify-cookie", tags=["Login & Register Owners and employeeds"])
async def verify_cookie(request: Request):
    token = request.cookies.get("access_token"),
    if not token:
        raise HTTPException(status_code=400, detail="Cookie no presente")
    return {"status": "Cookie válida"}

@router.get("/protected", tags=["Login & Register Owners and employeeds"])
async def protected_route(username: str = Depends(get_current_user)):
    print("🧪 Usuario autenticado:", username)
    return {"message": f"Hello, {username}! This is a protected resource."}

@router.get("/logout", tags=["Login & Register Owners and employeeds"])
async def logout(current_user: str = Depends(get_current_user)):
    return {"message": f"Logged out {current_user}"}

@router.get("/getUsers", tags=["Login & Register Owners and employeeds"])
async def get_users():
    try:
        with engine.begin() as conn:
            result = conn.execute(text("SELECT * FROM credentials"))
            rows = result.mappings().all()
            if not rows:
                raise HTTPException(status_code=404, detail="No users found.")
            return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/getUserByID/{id}", tags=["Login & Register Owners and employeeds"])
async def get_user_by_id_endpoint(id: str):
    user = get_user_by_id(id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    return user

@router.put("/updateUser", tags=["Login & Register Owners and employeeds"])
async def update_user_endpoint(id: str, user: User):
    user_db = get_user_by_id(id)
    if not user_db:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )
    success = update_user(id, user.username, user.password, user.rol, user.local)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error updating user"
        )
    return {"message": "User updated successfully"}

@router.delete("/deleteUser", tags=["Login & Register Owners and employeeds"])
async def delete_user_endpoint(id: str):
    success = delete_user(id)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Error deleting user"
        )
    return {"message": "User deleted successfully"}

@router.get("/test-cookies", tags=["Test"])
async def test_cookies(request: Request):
    return {"cookies": dict(request.cookies)}

@router.post("/test-set-cookie-post", tags=["Test"])
async def test_set_cookie_post():
    access_token = create_access_token(
        data={"sub": "testuser"}
    )
    response = JSONResponse({"message": "Cookie de test (POST) seteada"})
    response.set_cookie(
        key="access_token" if IS_LOCAL else "Authorization",
        value=access_token,
        httponly=False if IS_LOCAL else True,
        secure=False if IS_LOCAL else True,
        samesite="lax" if IS_LOCAL else "none",
        max_age=3600,
        domain="localhost" if IS_LOCAL else "api-burgerli.iwebtecnology.com",  # <--- CORREGIDO
        path="/",
    )
    return response
