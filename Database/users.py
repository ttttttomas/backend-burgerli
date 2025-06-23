from typing import Optional
from models.user import UserDB, User
from Database.getConnection import getConnectionForLogin
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
import uuid

def get_user_by_username(username: str) -> Optional[UserDB]:
    """
    Obtiene un usuario de la base de datos por su username
    """
    db = getConnectionForLogin()
    if db is None:
        return None
    
    try:
        user = db.query(UserDB).filter(UserDB.username == username).first()
        return user
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        db.close()

def verify_user_credentials(username: str, password: str) -> bool:
    """
    Verifica las credenciales del usuario
    """
    user = get_user_by_username(username)
    if user is not None:
        # Convertir a string para evitar problemas con SQLAlchemy
        return str(user.password) == str(password)
    return False

def create_user(username: str, password: str) -> bool:
    """
    Crea un nuevo usuario en la base de datos
    """
    db = getConnectionForLogin()
    generated_id = str(uuid.uuid4())
    if db is None:
        return False
    
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(UserDB).filter(UserDB.username == username).first()
        if existing_user:
            return False
        
        # Crear nuevo usuario
        new_user = UserDB(id=generated_id, username=username, password=password)
        db.add(new_user)
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def delete_user(id: str):
    """
    Elimina un usuario de la base de datos
    """
    db = getConnectionForLogin()
    if db is None:
        return False
    
    try:
        user = db.query(UserDB).filter(UserDB.id == id).first()
        if not user:
            return False
        
        # Eliminar usuario
        db.delete(user)
        db.commit()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        db.rollback()
        return False
    finally:
        db.close()