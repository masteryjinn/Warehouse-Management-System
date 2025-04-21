from fastapi import APIRouter, Query, HTTPException, Depends
from config.token import verify_token
from auth.utils import get_user_config
from auth.database_customers import get_customers_function, count_total_customers, delete_customer_from_db, update_customer_function, get_customers_full
from auth.database_customers import add_customer_to_db
from auth.utils import check_access_admin_and_manager, check_acess_all_roles
customers_router = APIRouter()

@customers_router.get("/customers")
async def get_customers(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),  # Загальний пошук
    name_filter: str = Query(None),  # Фільтр по імені
    type_filter: str = Query(None),  # Фільтр по типу
    email_required: bool = Query(None),
    phone_required: bool = Query(None),
    address_required: bool = Query(None)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_access_admin_and_manager(user_id, role)  # Перевіряємо доступ

    USER_CONFIG = get_user_config(user_id)

    # Загальний підрахунок елементів
    total_items = count_total_customers(
        USER_CONFIG, search, name_filter, type_filter, email_required, phone_required, address_required
    )
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

    # Отримання списку користувачів з усіма фільтрами
    customers = get_customers_function(
        USER_CONFIG, page, limit, search, name_filter, type_filter, email_required, phone_required, address_required
    )

    return {
        "data": customers,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }

@customers_router.delete("/customers/{customer_id}")
async def remove_customer(customer_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_access_admin_and_manager(user_id, role)  
    if not customer_id:
        raise HTTPException(status_code=400, detail="ID клієнта обов'язковий для заповнення")
    
    USER_CONFIG = get_user_config(user_id)  
    result = delete_customer_from_db(USER_CONFIG, customer_id)
    if not result:
        raise HTTPException(status_code=500, detail="Не вдалося видалити клієнта з бази даних. Зачекайте, поки всі його замовлення будуть в статусі відправлені і повторіть спробу зновую")

    return {"message": "Клієнта видалено"}

@customers_router.put("/customers/{customer_id}")
async def update_customer(customer_id: int, data: dict, token_data: dict = Depends(verify_token)):
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
    update_customer_function(USER_CONFIG, customer_id, name, type, contacts)
    return {"message": "Дані клієнта оновлено"}

@customers_router.post("/customers")
async def create_customer(data: dict, token_data: dict = Depends(verify_token)):
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
    add_customer_to_db(USER_CONFIG, name, type, contacts)
    return {"message": "Клієнта успішно створено"}

@customers_router.get("/customers/select")
async def select_supplier(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG= get_user_config(user_id)
    suppliers=get_customers_full(USER_CONFIG)
    if not suppliers:
        raise HTTPException(status_code=404, detail="Постачальники не знайдені")
    return suppliers