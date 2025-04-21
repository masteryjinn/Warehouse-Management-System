import pymysql
from auth.database_utils import get_db_connection
from auth.database_auth import get_employee_id_by_user_id


def get_employee_info(employee_id, user_config):
    connection = get_db_connection(user_config)
    cursor = connection.cursor()
    
    try:
        query = "SELECT name, position FROM Employees WHERE employee_id = %s"
        cursor.execute(query, (employee_id,))
        result = cursor.fetchone()

        if result:
            return {
                "name": result[0],
                "position": result[1]
            }
        return None
    finally:
        cursor.close()
        connection.close()

def get_employee_contacts(employee_id, user_config):
    connection = get_db_connection(user_config)
    cursor = connection.cursor()
    
    try:
        query = "SELECT contact_type, contact_value FROM Contacts_employees WHERE employee_id = %s"
        cursor.execute(query, (employee_id,))
        contacts = cursor.fetchall()

        contact_info = {
            "email": "",
            "phone": "",
            "address": ""
        }

        for contact in contacts:
            if contact[0] == "email":
                contact_info["email"] = contact[1]
            elif contact[0] == "phone":
                contact_info["phone"] = contact[1]
            elif contact[0] == "address":
                contact_info["address"] = contact[1]

        return contact_info
    finally:
        cursor.close()
        connection.close()

def get_user_info_from_db(user_id, user_config):
    # Отримуємо employee_id з user_id
    employee_id = get_employee_id_by_user_id(user_id)
    if not employee_id:
        return None

    # Отримуємо основну інформацію про працівника
    employee_info = get_employee_info(employee_id, user_config)
    if not employee_info:
        return None

    # Отримуємо контактні дані
    contacts = get_employee_contacts(employee_id, user_config)
    if not contacts:
        return None
    return {
        "employee_id": employee_id,
        "name": employee_info["name"],
        "position": employee_info["position"],
        "email": contacts["email"],
        "phone": contacts["phone"],
        "address": contacts["address"]
    }