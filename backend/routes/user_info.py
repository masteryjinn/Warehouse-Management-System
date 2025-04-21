from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config.token import verify_token
from auth.database_auth import get_password_hash_by_user_id, get_username_by_id # Імпортуємо функцію для отримання хешу пароля
from auth.database_user_info import get_user_info_from_db  # Імпортуємо функцію для підключення до БД
from auth.utils import get_user_config, check_acess_all_roles

user_router = APIRouter()

# Модель для представлення інформації про користувача
class UserInfo(BaseModel):
    employee_id: int
    name: str
    position: str | None
    email: str
    phone: str
    address: str

@user_router.get("/user/info", response_model=UserInfo)
async def get_user_info(token_data: dict = Depends(verify_token)):  
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    if not user_id:
        raise HTTPException(status_code=400, detail="Некоректний токен")
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача
    user_info = get_user_info_from_db(user_id, USER_CONFIG)  # Отримуємо інформацію про користувача з БД

    if not user_info:
        raise HTTPException(status_code=404, detail="Користувач не знайдений")

    return user_info

