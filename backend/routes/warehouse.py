from fastapi import APIRouter, Query, HTTPException, Depends
from config.token import verify_token
from auth.utils import check_acess_all_roles, check_access_admin_and_manager, check_access_admin
from auth.utils import get_user_config
from auth.database_warehouse import get_all_sections_function, count_total_sections, get_sections_function, add_section_to_db
from auth.database_warehouse import update_section_function, delete_section_from_db
from typing import List

warehouse_router = APIRouter()

@warehouse_router.get("/sections/full")
async def get_sections(
    token_data: dict = Depends(verify_token),
):
    # Перевірка доступу
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)  # Перевірка доступу для всіх ролей
    USER_CONFIG = get_user_config(user_id)
    # Отримання секцій
    sections = get_all_sections_function(USER_CONFIG)
    
    # Якщо не знайдено секцій, повертаємо помилку
    if not sections:
        raise HTTPException(status_code=404, detail="Sections not found")
    
    return {"sections": sections}

@warehouse_router.get("/sections")
async def get_sections(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),  # Загальний пошук
    is_empty: bool = Query(False),
):
    try:
        user_id = token_data.get("user_id")
        role = token_data.get("role")
        print(f"[get_sections] user_id={user_id}, role={role}, page={page}, limit={limit}, search={search}, is_empty={is_empty}")

        check_acess_all_roles(user_id, role)

        USER_CONFIG = get_user_config(user_id)
        print(f"[get_sections] is_empty_bool = {is_empty}")

        total_items = count_total_sections(USER_CONFIG, search, is_empty)
        print(f"[get_sections] total_items = {total_items}")

        total_pages = max((total_items + limit - 1) // limit, 1)
        if page > total_pages:
            raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

        sections = get_sections_function(USER_CONFIG, page, limit, search, is_empty)
        print(f"[get_sections] sections count = {len(sections)}")

        return {
            "data": sections,
            "total_pages": total_pages,
            "total_items": total_items,
            "current_page": page
        }
    except Exception as e:
        print(f"[get_sections] ERROR: {e}")
        raise HTTPException(status_code=500, detail="Помилка сервера при отриманні секцій")

@warehouse_router.post("/sections")
async def create_section(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")
    check_access_admin(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    name = data.get("name")
    location = data.get("location")
    employee_name= data.get("employee_name")
    add_section_to_db(USER_CONFIG, name, location,employee_name)
    return {"message": "Секцію успішно створено"}

@warehouse_router.delete("/sections/{section_id}")
async def remove_section(section_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_access_admin(user_id, role)  
    if not section_id:
        raise HTTPException(status_code=400, detail="ID секції обов'язковий для заповнення")
    
    USER_CONFIG = get_user_config(user_id)  
    result = delete_section_from_db(USER_CONFIG, section_id)
    if not result:
        raise HTTPException(status_code=500, detail="Не вдалося видалити секцію з бази даних")

    return {"message": "Секцію видалено"}

@warehouse_router.put("/sections/{section_id}")
async def update_section(section_id : int, data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")  # Отримуємо роль з токена
    check_access_admin(user_id, role)  # Перевіряємо доступ
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача
    name = data.get("name")
    location = data.get("location")
    employee_name= data.get("employee_name")
    update_section_function(USER_CONFIG, section_id, name, location,employee_name)
    return {"message": "Дані секції оновлено"}
