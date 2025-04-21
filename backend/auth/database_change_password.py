from config.config import DB_CONFIG_AUTH, DB_CONFIG_ADMIN, DB_CONFIG_CHANGE_PASSWORD
import pymysql
from auth.database_auth import get_db_connection
import hashlib

# Функція для отримання айді працівника за email
def get_employee_id_by_email(email):
    query = """
    SELECT c.employee_id
    FROM Contacts_employees c
    WHERE c.contact_type = 'email' AND c.contact_value = %s
    """
    # Підключення до бази
    connection = get_db_connection(DB_CONFIG_CHANGE_PASSWORD) 
    cursor = connection.cursor()

    try:
        cursor.execute(query, (email,))
        employee_id = cursor.fetchone()

        # Перевірка, чи знайдено користувача
        if employee_id is None:
            return None

        # Повертаємо перший елемент з кортежу
        return employee_id[0]

    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return None

    finally:
        cursor.close()
        connection.close()

def perform_password_reset(employee_id, new_password_hash):
    connection = get_db_connection(DB_CONFIG_CHANGE_PASSWORD)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        # Перевірка наявності облікового запису для працівника
        query_check = "SELECT user_id FROM Users WHERE employee_id = %s"
        cursor.execute(query_check, (employee_id,))
        user = cursor.fetchone()

        if not user:
            print(f"Обліковий запис для employee_id {employee_id} не знайдено.")
            return False

        # Якщо є — оновлюємо пароль
        query_update = """
        UPDATE Users
        SET password_hash = %s, is_temp_password = TRUE
        WHERE employee_id = %s
        """
        cursor.execute(query_update, (new_password_hash, employee_id))
        connection.commit()

        print("Пароль успішно змінено.")
        return True

    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return False

    finally:
        cursor.close()
        connection.close()


def update_user_password(username, new_password):
    """Оновлює пароль у Users і MySQL (якщо користувач існує)"""
    
    # SQL-запит для оновлення пароля в Users
    user_update_query = """
    UPDATE Users
    SET password_hash = %s, is_temp_password = FALSE
    WHERE username = %s
    """

    # SQL-запит для перевірки існування користувача у MySQL
    check_user_query = "SELECT COUNT(*) FROM mysql.user WHERE user = %s"

    # SQL-запит для зміни пароля користувача у MySQL
    alter_user_query = f"ALTER USER %s@'localhost' IDENTIFIED BY %s"

    connection = get_db_connection(DB_CONFIG_ADMIN)
    cursor = connection.cursor()

    try:
        # Хешування нового пароля
        new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        # Оновлення пароля у таблиці Users
        cursor.execute(user_update_query, (new_password_hash, username))
        
        # Перевірка, чи змінено хоча б один рядок(якщо паролі однакові, то поверне це)
        if cursor.rowcount == 0:
            connection.rollback()
            return {"success": False, "message": f"Пароль повинен відрізнятися від минулого"}

        # Перевірка існування користувача в MySQL
        cursor.execute(check_user_query, (username,))
        user_exists = cursor.fetchone()[0]

        if user_exists:
            # Зміна пароля в MySQL
            cursor.execute(alter_user_query, (username, new_password_hash))
        
        connection.commit()
        return {"success": True, "message": "Пароль успішно змінено"}

    except pymysql.MySQLError as err:
        connection.rollback()
        return {"success": False, "message": f"Помилка MySQL: {err}"}

    finally:
        cursor.close()
        connection.close()