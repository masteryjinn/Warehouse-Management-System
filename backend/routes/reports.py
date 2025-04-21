# main.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth.database_reports import get_report_data, create_report_entry
from typing import Optional
from auth.utils import get_user_config, check_access_admin
from config.token import verify_token
from datetime import date

report_router = APIRouter()

@report_router.get("/orders/report")
async def get_orders_report(
    start_date: date,
    end_date: date,
    status: str,
    category: Optional[str] = None,
    token_data: dict = Depends(verify_token),
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_access_admin(user_id, role)
    
    USER_CONFIG = get_user_config(user_id)
    
    report_type = "Звіт по замовленнях"  # Тип звіту

    report_id = create_report_entry(USER_CONFIG,report_type, user_id, role)
    print("ID звіту:", report_id)


    data, total_orders, total_items, total_revenue = get_report_data(
        USER_CONFIG, start_date, end_date, status, category
    )

    return {
        "data": data,
        "total_orders": total_orders,
        "total_items": total_items,
        "total_revenue": total_revenue,
    }
