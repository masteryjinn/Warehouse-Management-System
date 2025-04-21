from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import hashlib

from auth.database_auth import get_user
from config.token import create_jwt_token

authorization_router = APIRouter()

# Модель для входу
class LoginRequest(BaseModel):
    username: str
    password: str

@authorization_router.post("/login/")
async def login(request: LoginRequest):
    user_data = get_user(request.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")

    stored_hash, role, user_id, is_temp_password = user_data

    # Перевірка пароля
    if hashlib.sha256(request.password.encode()).hexdigest() == stored_hash:
        # Призначаємо роль користувачу

        # Створення токену
        token = None
        if is_temp_password==0:
            token = create_jwt_token(user_id, role)
        
        # Повернення токену та імені працівника
        return {
            "token": token,
            "role": role,
            "is_temp_password": is_temp_password
        }
    
    raise HTTPException(status_code=401, detail="Невірний пароль")