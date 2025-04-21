from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config.token import verify_token
from auth.database_auth import  get_username_by_emp_id, get_user_id_by_emp_id
from auth.utils import get_hash_password
from auth.database_employees import add_user_to_db, get_employees_function, delete_employee_function, update_employee_function
from auth.database_employees import add_employee_function, register_user_in_db, delete_user_from_db, get_employees_full
from auth.database_employees import count_total_employees, update_user_role_in_db, grant_role_to_user, delete_employee_account_function
from fastapi import Query
from auth.utils import get_user_config, check_access_admin

employees_router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str

@employees_router.post("/employees/register/{emp_id}")
async def register_user(emp_id: int, request: RegisterRequest, token_data: dict = Depends(verify_token)):
    """
    Реєстрація користувача (створення запису користувача)
    :param emp_id: ID співробітника
    :param request: дані для реєстрації (username, password)
    :param token: Токен для перевірки автентичності
    """
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")  # Отримуємо роль з токена
    check_access_admin(user_id, role)  # Перевіряємо доступ
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача

    # Отримуємо дані з запиту
    username_r = request.username
    password_r = request.password
    role_r = request.role
    # Перевірка наявності ID співробітника
    if not emp_id:
        raise HTTPException(status_code=400, detail="ID співробітника обов'язковий для заповнення")    

    # Перевірка наявності пароля та імені користувача
    if not username_r or not password_r:
        raise HTTPException(status_code=400, detail="Логін та пароль обов'язкові для заповнення")

    # Хешуємо пароль для безпечного зберігання в базі
    password_hash_r = get_hash_password(password_r)

    # Додаємо нового користувача до бази даних
    user_added = add_user_to_db(USER_CONFIG, username_r, password_hash_r, emp_id, role_r)

    if not user_added:
        raise HTTPException(status_code=500, detail="Не вдалося зареєструвати користувача")
    
    user_registered = register_user_in_db(username_r, password_hash_r, role_r)

    if not user_registered:
        raise HTTPException(status_code=500, detail="Не вдалося зареєструвати користувача в базі даних")
    # Якщо користувача успішно додано, повертаємо успішну відповідь
    return {"message": "Користувача успішно зареєстровано"}

@employees_router.get("/employees")
async def get_employees(
    token_data: dict = Depends(verify_token),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(None),
    registered_only: bool = Query(False)
):
    user_id = token_data.get("user_id")
    role = token_data.get("role")

    check_access_admin(user_id, role)  

    USER_CONFIG = get_user_config(user_id)

    total_items = count_total_employees(USER_CONFIG, search, registered_only)
    total_pages = max((total_items + limit - 1) // limit, 1)

    if page > total_pages:
        raise HTTPException(status_code=400, detail="Сторінка виходить за межі")

    employees = get_employees_function(USER_CONFIG, page, limit, search, registered_only)

    return {
        "data": employees,
        "total_pages": total_pages,
        "total_items": total_items,
        "current_page": page
    }


@employees_router.put("/employees/{emp_id}")
async def update_employee(emp_id: int, data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")  # Отримуємо роль з токена
    check_access_admin(user_id, role)  # Перевіряємо доступ
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача
    name = data.get("name")
    position = data.get("position")
    contacts = {
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address")
    }
    update_employee_function(USER_CONFIG, emp_id, name, position, contacts)
    return {"message": "Дані співробітника оновлено"}


@employees_router.delete("/employees/{emp_id}")
async def remove_employee(emp_id: int, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_access_admin(user_id, role)

    if not emp_id:
        raise HTTPException(status_code=400, detail="ID співробітника обов'язковий для видалення")

    # Отримуємо username і user_id, якщо вони прив'язані
    username = get_username_by_emp_id(emp_id)
    user_id_emp = get_user_id_by_emp_id(emp_id)

    if user_id_emp == user_id:
        raise HTTPException(status_code=400, detail="Не можна видалити самого себе")

    USER_CONFIG = get_user_config(user_id)

    # Видаляємо працівника у будь-якому випадку
    delete_employee_function(USER_CONFIG, emp_id)

    # Якщо користувач був зареєстрований — пробуємо видалити акаунт
    if username:
        user_deleted = delete_user_from_db(username)
        user_deleted2=delete_employee_account_function(USER_CONFIG, emp_id)
        if not user_deleted and not user_deleted2:
            raise HTTPException(status_code=500, detail="Співробітника видалено, але не вдалося видалити обліковий запис користувача")
        return {"message": "Зареєстрованого співробітника та його обліковий запис успішно видалено"}
    else:
        return {"message": "Незареєстрованого співробітника успішно видалено"}

@employees_router.post("/employees")
async def add_employee(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")  # Отримуємо user_id з токена
    role = token_data.get("role")
    check_access_admin(user_id, role)  # Перевіряємо доступ
    
    USER_CONFIG = get_user_config(user_id)  # Отримуємо конфігурацію користувача
    name = data.get("name")
    position = data.get("position")
    contacts = {
        "email": data.get("email"),
        "phone": data.get("phone"),
        "address": data.get("address")
    }
    add_employee_function(USER_CONFIG, name, position, contacts)
    return {"message": "Співробітника додано"}

@employees_router.post("/employees/update_role")
async def update_role(data: dict, token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_access_admin(user_id, role) 

    employee_id = data.get("employee_id")
    new_role = data.get("new_role")
    user_id_employee_id = get_user_id_by_emp_id(employee_id)  
    if user_id_employee_id == user_id:
        raise HTTPException(status_code=400, detail="Не можна змінити роль самого себе") 
    if not employee_id or not new_role:
        raise HTTPException(status_code=400, detail="ID співробітника та нова роль обов'язкові")

    if new_role not in ["admin", "manager", "employee"]:
        raise HTTPException(status_code=400, detail="Некоректна роль")

    username = get_username_by_emp_id(employee_id)
    if not username:
        raise HTTPException(status_code=404, detail="Співробітника не знайдено")

    # Оновлення ролі в логічній таблиці Users
    user_config = get_user_config(user_id)
    if not update_user_role_in_db(user_config, employee_id, new_role):
        raise HTTPException(status_code=500, detail="Не вдалося оновити роль у таблиці користувачів")

    # Призначення ролі в MySQL (GRANT)
    if not grant_role_to_user(username, new_role):
        raise HTTPException(status_code=500, detail="Не вдалося призначити роль у MySQL")

    return {"message": f"Роль '{new_role}' успішно оновлено для користувача '{username}'"}

@employees_router.get("/employees/select")
async def get_employees_select(token_data: dict = Depends(verify_token)):
    user_id = token_data.get("user_id")
    role = token_data.get("role")
    check_access_admin(user_id, role)
    USER_CONFIG = get_user_config(user_id) 
    employees=get_employees_full(USER_CONFIG)
    if not employees:
        raise HTTPException(status_code=404, detail="Постачальники не знайдені")
    return employees