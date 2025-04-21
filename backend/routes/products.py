from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from enum import Enum
from config.token import verify_token
from auth.utils import get_user_config
from auth.database_products import get_products_function, count_total_products, delete_product_from_db, update_product_function
from auth.database_products import add_product_to_db, fetch_available_products_from_db, get_product_by_id
from auth.database_products import get_categories_function, get_products_full_function,fetch_all_products_from_db
from auth.utils import check_acess_all_roles

class SortOrder(str, Enum):
    price_asc = "price_asc"
    price_desc = "price_desc"
    quantity_asc = "quantity_asc"
    quantity_desc = "quantity_desc"
    name_asc = "name_asc"
    name_desc = "name_desc"
    expiration_date_asc = "expiration_date_asc"
    expiration_date_desc = "expiration_date_desc"

products_router = APIRouter()

@products_router.get("/products")
async def get_products(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    expire_date: bool = Query(False),
    has_expired: bool = Query(False),
    section: str = Query(None),
    name_filter: str = Query(None),
    category_filter: Optional[List[str]] = Query(default=None),
    price_min: float = Query(None),
    price_max: float = Query(None),
    sort_order: SortOrder = Query("price_asc")
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_acess_all_roles(user_id, role)

    USER_CONFIG = get_user_config(user_id)

    # Додатковий захист
    if isinstance(category_filter, str):
        category_filter = [category_filter]

    print("Категорії:", category_filter)

    total_items = count_total_products(
        USER_CONFIG, search,expire_date, has_expired, section, name_filter, category_filter, price_min, price_max
    )
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

    products = get_products_function(
        USER_CONFIG, page, limit, search, expire_date, has_expired, section, name_filter, category_filter, price_min, price_max, sort_order
    )
    return {
        "data": products,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }

@products_router.get("/products/full")
async def get_products_full(
    token_data: dict = Depends(verify_token),
    search: str = Query(None),
    expire_date: bool = Query(False),
    has_expired: bool = Query(False),
    section: str = Query(None),
    name_filter: str = Query(None),
    category_filter: Optional[List[str]] = Query(default=None),
    price_min: float = Query(None),
    price_max: float = Query(None),
    sort_order: SortOrder = Query("price_asc")
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_acess_all_roles(user_id, role)

    USER_CONFIG = get_user_config(user_id)


    products = get_products_full_function(
        USER_CONFIG, search, expire_date, has_expired, section, name_filter, category_filter, price_min, price_max, sort_order
    )
    return {"products": products}

@products_router.delete("/products/{product_id}")
async def remove_product(product_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)

    if not product_id:
        raise HTTPException(status_code=400, detail="ID продукту обов'язковий для заповнення")

    USER_CONFIG = get_user_config(user_id)
    try:
        result = delete_product_from_db(USER_CONFIG, product_id)
        if not result:
            raise HTTPException(status_code=500, detail="Не вдалося видалити продукт з бази даних")
    except HTTPException:
        raise  # просто прокидаємо далі
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Невідома помилка: {str(e)}")

    return {"message": "Продукт успішно видалено"}

    
@products_router.put("/products/{product_id}")
async def update_product(product_id: int, data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    if not product_id:
        raise HTTPException(status_code=400, detail="ID продукту обов'язковий для заповнення")
    name = data.get("name")
    category = data.get("category")
    price = data.get("price")
    quantity = data.get("quantity")
    description = data.get("description")
    unit= data.get("unit")
    experation_date= data.get("expiry_date")
    supplier_name= data.get("supplier")
    res=update_product_function(USER_CONFIG, product_id, name, category, price, quantity, description, unit, experation_date, supplier_name)
    if not res:
        raise HTTPException(status_code=500, detail="Не вдалося оновити продукт")
    return {"message": "Дані продукту оновлено"}

@products_router.post("/products")
async def add_product(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    name = data.get("name")
    category = data.get("category")
    price = data.get("price")
    quantity = data.get("quantity")
    description = data.get("description")
    unit= data.get("unit")
    experation_date= data.get("expiry_date")
    supplier_name= data.get("supplier")
    res=add_product_to_db(USER_CONFIG, name, category, price, quantity, description, unit, experation_date, supplier_name)
    if not res:
        raise HTTPException(status_code=500, detail="Не вдалося додати продукт")
    return {"message": "Продукт додано"}

@products_router.get("/products/categories")
async def get_categories(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    categories = get_categories_function(USER_CONFIG)
    if not categories:
        raise HTTPException(status_code=500, detail="Не вдалося отримати категорії")
    return {"categories": categories}

@products_router.get("/products/available")
async def get_available_products(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    try:
        return fetch_available_products_from_db(USER_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@products_router.get("/products/all")
async def get_available_products(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    try:
        return fetch_all_products_from_db(USER_CONFIG)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@products_router.get("/products/{product_id}")
def fetch_product(product_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_acess_all_roles(user_id, role)
    USER_CONFIG = get_user_config(user_id)
    product = get_product_by_id(USER_CONFIG, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Продукт не знайдено")
    return product