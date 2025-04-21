import hashlib
import random
import string
from config.config import TEMP_PASSWORD_LENGTH

from fastapi import HTTPException
from auth.database_auth import get_password_hash_by_user_id, get_username_by_id  # Імпортуємо функцію для отримання хешу пароля

import hashlib

def generate_encrypted_report_type(report_type: str, user_id: int, role: str):
    # Створюємо комбінований рядок
    combined_string = f"{report_type}_{user_id}_{role}"
    
    # Використовуємо хешування (SHA256, або інший алгоритм за потребою)
    hashed_report_type = hashlib.sha256(combined_string.encode('utf-8')).hexdigest()
    
    return hashed_report_type

# Функція для перевірки пароля
def verify_password(input_password, stored_hash):
    return stored_hash == hashlib.sha256(input_password.encode()).hexdigest()

# Генерація тимчасового пароля
def generate_temp_password():
    characters = string.ascii_letters + string.digits
    temp_password = ''.join(random.choice(characters) for i in range(TEMP_PASSWORD_LENGTH))
    return temp_password

def get_hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Функція для отримання конфігурації користувача
def get_user_config(user_id: int) -> dict:
    password_hash = get_password_hash_by_user_id(user_id)

    if not password_hash:
        raise HTTPException(status_code=404, detail="Користувача не знайдено")
    
    username = get_username_by_id(user_id)  

    user_config = {
        "host": "localhost",  # Хост бази даних
        "user": username,  # Логін до бази даних
        "password": password_hash,  # Пароль
        "database": "WarehouseDB",  # Назва бази даних
    }
    
    return user_config

def check_access_admin_and_manager(user_id: int, role: str):
    if role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Недостатньо прав для виконання цієї дії")
    if not user_id:
        raise HTTPException(status_code=400, detail="Некоректний токен")
    
def check_access_admin(user_id: int, role: str):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Недостатньо прав для виконання цієї дії")
    if not user_id:
        raise HTTPException(status_code=400, detail="Некоректний токен")

def check_access_manager(user_id: int, role: str):
    if role != "manager":
        raise HTTPException(status_code=403, detail="Недостатньо прав для виконання цієї дії")
    if not user_id:
        raise HTTPException(status_code=400, detail="Некоректний токен")
    
def check_acess_all_roles(user_id: int, role: str):
    if role not in ["admin", "manager", "employee"]:
        raise HTTPException(status_code=403, detail="Недостатньо прав для виконання цієї дії")
    if not user_id:
        raise HTTPException(status_code=400, detail="Некоректний токен")

# Функція для виконання SQL запиту
"""def execute_query(connection, query, params=None):
    cursor = connection.cursor()
    cursor.execute(query, params) if params else cursor.execute(query)
    connection.commit()
    cursor.close()
    connection.close()
"""
   

