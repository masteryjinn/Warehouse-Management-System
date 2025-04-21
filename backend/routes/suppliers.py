from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List
from config.token import verify_token
from auth.utils import get_user_config
from auth.database_suppliers import get_suppliers_function, count_total_suppliers, delete_supplier_from_db, update_supplier_function
from auth.database_suppliers import add_supplier_to_db, get_suppliers_full
from auth.utils import check_access_admin_and_manager, check_acess_all_roles

suppliers_router = APIRouter()

@suppliers_router.get("/suppliers")
async def get_suppliers(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),  # Загальний пошук
    name_filter: str = Query(None),  # Фільтр по імені
    type_filter: List[str] = Query(None),  # Список типів
    email_required: bool = Query(None),
    phone_required: bool = Query(None),
    address_required: bool = Query(None)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_access_admin_and_manager(user_id, role)  # Перевіряємо доступ

    USER_CONFIG = get_user_config(user_id)

    # Загальний підрахунок елементів
    total_items = count_total_suppliers(
        USER_CONFIG, search, name_filter, type_filter, email_required, phone_required, address_required
    )
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

    # Отримання списку користувачів з усіма фільтрами
    suppliers = get_suppliers_function(
        USER_CONFIG, page, limit, search, name_filter, type_filter, email_required, phone_required, address_required
    )

    return {
        "data": suppliers,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }

@suppliers_router.delete("/suppliers/{supplier_id}")
async def remove_suplier(supplier_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_access_admin_and_manager(user_id, role)  
    if not supplier_id:
        raise HTTPException(status_code=400, detail="ID постачальника обов'язковий для заповнення")
    
    USER_CONFIG = get_user_config(user_id)  
    result = delete_supplier_from_db(USER_CONFIG, supplier_id)
    if not result:
        raise HTTPException(status_code=500, detail="Не вдалося видалити постачальника з бази даних")

    return {"message": "Постачальника видалено"}

@suppliers_router.put("/suppliers/{supplier_id}")
async def update_suplier(supplier_id: int, data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")  # Отримуємо роль з токена
    check_access_admin_and_manager(user_id, role)  # Перевіряємо доступ
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача
    name = data.get("name")
    type = data.get("type")
    contacts = {
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address")
    }
    res=update_supplier_function(USER_CONFIG, supplier_id, name, type, contacts)
    if not res:
        raise HTTPException(status_code=500, detail="Не вдалося оновити дані постачальника")
    return {"message": "Дані постачальника оновлено"}

@suppliers_router.post("/suppliers")
async def create_supplier(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")
    check_access_admin_and_manager(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    name = data.get("name")
    type = data.get("type")
    contacts = {
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address")
    }
    add_supplier_to_db(USER_CONFIG, name, type, contacts)
    return {"message": "Постачальника успішно створено"}

@suppliers_router.get("/suppliers/select")
async def select_supplier(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG= get_user_config(user_id)
    suppliers=get_suppliers_full(USER_CONFIG)
    if not suppliers:
        raise HTTPException(status_code=404, detail="Постачальники не знайдені")
    return suppliers