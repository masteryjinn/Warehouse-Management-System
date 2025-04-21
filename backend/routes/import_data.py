from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from auth.utils import get_user_config, check_acess_all_roles
from config.token import verify_token
from typing import List, Dict
from auth.database_import import insert_employees, insert_customers, insert_suppliers

import_router = APIRouter()

class ImportRequest(BaseModel):
    data: List[Dict]

@import_router.post("/import/employees")
def import_employees(request: ImportRequest, token_data: dict = Depends(verify_token)):
    try:
        user_id = token_data.get("user_id")  # Отримуємо user_id з токена
        role = token_data.get("role")
        check_acess_all_roles(user_id, role)
        USER_CONFIG = get_user_config(user_id)
        insert_employees(USER_CONFIG,request.data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@import_router.post("/import/customers")
def import_customers(request: ImportRequest, token_data: dict = Depends(verify_token)):
    try:
        user_id = token_data.get("user_id")  # Отримуємо user_id з токена
        role = token_data.get("role")
        check_acess_all_roles(user_id, role)
        USER_CONFIG = get_user_config(user_id)
        insert_customers(USER_CONFIG,request.data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@import_router.post("/import/suppliers")
def import_suppliers(request: ImportRequest, token_data: dict = Depends(verify_token)):
    try:
        user_id = token_data.get("user_id")  # Отримуємо user_id з токена
        role = token_data.get("role")
        check_acess_all_roles(user_id, role)
        USER_CONFIG = get_user_config(user_id)
        insert_suppliers(USER_CONFIG,request.data)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
