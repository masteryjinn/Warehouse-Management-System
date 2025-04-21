from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List
from pydantic import BaseModel
from config.token import verify_token
from auth.utils import get_user_config
from auth.utils import check_access_admin_and_manager, check_acess_all_roles
from auth.database_orders import count_total_orders, get_orders_function, add_order_to_db, delete_orders_from_db, update_order_status_function
from auth.database_orders import confirm_order_in_db, get_order_details_from_db

orders_router = APIRouter()

class OrderItem(BaseModel):
    product_id: int
    quantity: int
    unit: str
    price: float
    section: str

class ConfirmOrderRequest(BaseModel):
    items: List[OrderItem]

@orders_router.get("/orders")
async def get_suppliers(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),  # Загальний пошук
    customer_name_filter: str = Query(None),  # Фільтр по імені
    status_filter: List[str] = Query(None),  # Список типів
    date_min: str = Query(None),
    date_max: str = Query(None)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_acess_all_roles(user_id, role)  # Перевіряємо доступ

    USER_CONFIG = get_user_config(user_id)

    # Загальний підрахунок елементів
    total_items = count_total_orders(
        USER_CONFIG, search, customer_name_filter, status_filter, date_min, date_max 
    )
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить   за межі")

    # Отримання списку користувачів з усіма фільтрами
    suppliers = get_orders_function(
        USER_CONFIG, page, limit, search, customer_name_filter, status_filter, date_min, date_max 
    )

    return {
        "data": suppliers,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }

@orders_router.post("/orders")
async def create_order(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    customer_name = data.get("customer_name")
    date = data.get("date")
    add_order_to_db(USER_CONFIG, customer_name, date)
    return {"message": "Замовлення успішно створено"}

@orders_router.delete("/orders/{order_id}")
async def remove_order(order_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_acess_all_roles(user_id, role)  
    if not order_id:
        raise HTTPException(status_code=400, detail="ID замовленя обов'язковий для заповнення")
    
    USER_CONFIG = get_user_config(user_id)  
    result = delete_orders_from_db(USER_CONFIG, order_id)
    if not result:
        raise HTTPException(status_code=500, detail="Не вдалося видалити замовлення з бази даних")

    return {"message": "Секцію видалено"}

@orders_router.put("/orders/{order_id}")
async def update_order_status(order_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_acess_all_roles(user_id, role)  
    if not order_id:
        raise HTTPException(status_code=400, detail="ID замовленя обов'язковий для заповнення")
    
    USER_CONFIG = get_user_config(user_id)  
    new_status = update_order_status_function(USER_CONFIG, order_id)
    return {"message": f"Статус замовлення оновлено до '{new_status}'"}

@orders_router.post("/orders/{order_id}/confirm")
async def confirm_order(
    order_id: int,
    data: ConfirmOrderRequest,
    token_data: dict = Depends(verify_token)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    
    # Перевірка прав
    check_acess_all_roles(user_id, role)
    
    # Конфіг користувача (наприклад, підключення до його бази)
    USER_CONFIG = get_user_config(user_id)
    
    # Оновлення статусу замовлення та додавання товарів
    confirm_order_in_db(USER_CONFIG, order_id, data.items)

    return {"message": f"Замовлення №{order_id} підтверджено та переведено в статус 'processing'"}

@orders_router.get("/orders/{order_id}/details")
async def get_order_details(order_id: int,token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    
    # Перевірка прав
    check_acess_all_roles(user_id, role)
    
    # Конфіг користувача (наприклад, підключення до його бази)
    USER_CONFIG = get_user_config(user_id)
    try:
        result = get_order_details_from_db(USER_CONFIG,order_id)

        if not result:
            raise HTTPException(status_code=404, detail="Замовлення не знайдено")

        # Формуємо відповідь для користувача
        order_details = []
        for row in result:
            order_details.append({
                "product_id": row[1],
                "product_name": row[2],
                "unit": row[3],
                "quantity": row[4],
                "price": row[5],
                "section_name": row[6]
            })

        return order_details

    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))