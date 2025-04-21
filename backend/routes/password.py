from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import hashlib
from config.token import verify_token, create_jwt_token 
from auth.database_change_password import get_employee_id_by_email, perform_password_reset, update_user_password
from auth.utils import generate_temp_password
from auth.database_auth import get_user_id_and_role, get_username_by_id

password_router = APIRouter()

# Модель для відновлення пароля
class PasswordResetRequest(BaseModel):
    email: str

class PasswordUpdateAfterResetRequest(BaseModel):
    username: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    new_password: str

@password_router.post("/change-password/")
async def change_password(request: ChangePasswordRequest, token_data: dict = Depends(verify_token)):
    user_id = token_data["user_id"]
    username = get_username_by_id(user_id)
    if not username:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    if not request.new_password:
        raise HTTPException(status_code=400, detail="Пароль не може бути пустим")

    # Оновлення пароля в базі даних
    result = update_user_password(username, request.new_password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])  
    
    return {"message": "Пароль успішно змінено"}

@password_router.post("/change-password-after-reset/")
async def change_password(request: PasswordUpdateAfterResetRequest):
    """Обробник запиту на зміну пароля після скидання"""
    
    # Перевірка вхідних даних
    if not request.new_password:
        raise HTTPException(status_code=400, detail="Пароль не може бути пустим")
    if not request.username:
        raise HTTPException(status_code=400, detail="Відсутні дані користувача")

    # Викликаємо функцію оновлення пароля
    result = update_user_password(request.username, request.new_password)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])

    user_data=get_user_id_and_role(request.username)
    if not user_data:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    token = create_jwt_token(user_data["user_id"], user_data["role"])
    if not token:
        raise HTTPException(status_code=500, detail="Не вдалося створити токен")
    return {"message": result["message"], "token": token}

@password_router.post("/reset-password/")  
async def reset_password(request: PasswordResetRequest):
    employee_id = get_employee_id_by_email(request.email)
    if employee_id is None:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    
    new_password = generate_temp_password()
    hashed_password = hashlib.sha256(new_password.encode()).hexdigest()
    result = perform_password_reset(employee_id, hashed_password)
    if not result:
        raise HTTPException(status_code=500, detail="Не вдалося скинути пароль. Користувача не знайдено.")
    
    return {"message": "Тимчасовий пароль надіслано на вашу електронну пошту", "temp_password": new_password}


