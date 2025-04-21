import pymysql
from auth.database_utils import get_db_connection
from config.config import DB_CONFIG_ADMIN

def register_user_in_db(username: str, password_hash: str, role: str) -> bool:
    """
    Функція для реєстрації нового користувача в базі даних MySQL.
    :param username: Ім'я користувача
    :param password_hash: Хеш пароля
    :param role: Роль користувача
    :return: True, якщо користувача успішно зареєстровано, інакше False
    """
    connection = get_db_connection(DB_CONFIG_ADMIN)
    if connection is None:
        print("Не вдалося підключитися до бази даних")
        return False

    try:
        with connection.cursor() as cursor:
            # Створення користувача в базі даних MySQL
            sql_create_user = f"CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password_hash}'"
            cursor.execute(sql_create_user)
            
            # Призначення ролі користувачу в БД
            if role == 'admin':
                cursor.execute("GRANT 'admin_role' TO %s@'localhost'", (username,))
                cursor.execute("SET DEFAULT ROLE 'admin_role' TO %s@'localhost'", (username,))
            elif role == 'manager':
                cursor.execute("GRANT 'manager_role' TO %s@'localhost'", (username,))
                cursor.execute("SET DEFAULT ROLE 'manager_role' TO %s@'localhost'", (username,))
            elif role == 'employee':
                cursor.execute("GRANT 'employee_role' TO %s@'localhost'", (username,))
                cursor.execute("SET DEFAULT ROLE 'employee_role' TO %s@'localhost'", (username,))
        
        # Підтвердження змін
        connection.commit()
        print(f"Користувача '{username}' успішно зареєстровано з роллю '{role}'")
        return True
    
    except pymysql.MySQLError as e:
        print(f"Помилка реєстрації користувача: {e}")
        connection.rollback()  # Відкат транзакції в разі помилки
        return False
    
    finally:
        connection.close()  # Закриваємо з'єднання з базою даних

# Приклад реєстрації користувача
username = 'ivan.petrenko2'
password_hash = 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f'  # Замініть на реальний хеш пароля
role = 'employee'  # Роль користувача (може бути 'admin', 'manager', або 'employee')

result = register_user_in_db(username, password_hash, role)
if result:
    print("Користувача зареєстровано успішно.")
else:
    print("Сталася помилка при реєстрації користувача.")