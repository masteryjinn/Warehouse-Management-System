from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List
from typing import Optional
from datetime import date
from config.token import verify_token
from auth.utils import get_user_config
from auth.utils import check_access_admin_and_manager, check_acess_all_roles
from auth.database_stock_movements import add_income_items_to_db, IncomingItem, get_stock_movements,count_stock_movements
from auth.database_stock_movements import RelocationRequest, relocate_items, RelocationItem

stock_movements_router = APIRouter()

@stock_movements_router.post("/stock_movements/relocation")
async def relocate_stock(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_access_admin_and_manager(user_id, role)

    section_id = data.get("section_id")
    items_data = data.get("items", [])

    if not section_id or not items_data:
        raise HTTPException(status_code=400, detail="Неповні дані для переміщення")

    try:
        items = [RelocationItem(**item) for item in items_data]
        USER_CONFIG = get_user_config(user_id)
        relocate_items(USER_CONFIG, section_id, items)

        return {"message": "Переміщення виконано успішно"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Внутрішня помилка сервера")

@stock_movements_router.post("/stock_movements")
async def add_income(items: List[IncomingItem], token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id") 
    role = token_data.get("role")  
    check_access_admin_and_manager(user_id, role)  
    try:
        USER_CONFIG = get_user_config(user_id)  
        add_income_items_to_db(USER_CONFIG, items)
        return {"message": "Надходження успішно додано"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print("[SERVER ERROR]:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    
@stock_movements_router.get("/stock_movements")
async def get_stock_movements_endpoint(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    movement_type: Optional[str] = Query(None),
    product_id: Optional[int] = Query(None),
    section_id: Optional[int] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    quantity_min: Optional[int] = Query(None),
    quantity_max: Optional[int] = Query(None)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_access_admin_and_manager(user_id, role)
    USER_CONFIG = get_user_config(user_id)

    total_items = count_stock_movements(USER_CONFIG, movement_type, product_id, section_id, date_from, date_to, quantity_min, quantity_max)
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

    items = get_stock_movements(USER_CONFIG, page, limit, movement_type, product_id, section_id, date_from, date_to, quantity_min, quantity_max)

    return {
        "items": items,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }
