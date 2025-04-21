import os

DB_AUTH_PASSWORD = os.getenv("DB_AUTH_PASSWORD")
DB_CHANGE_PASSWORD = os.getenv("DB_CHANGE_PASSWORD")
DB_ADMIN_PASSWORD = os.getenv("DB_ADMIN_PASSWORD")

DB_CONFIG_AUTH = {
    "host": "localhost",  # Хост бази даних
    "user": "auth_reader",  #Логін до бази даних
    "password": DB_AUTH_PASSWORD,  #Пароль
    "database": "WarehouseDB",  # Назва  бази даних
}

DB_CONFIG_CHANGE_PASSWORD = {
    "host": "localhost",  # Хост бази даних
    "user": "password_reset_user",  #Логін до бази даних
    "password": DB_CHANGE_PASSWORD,  #Пароль
    "database": "WarehouseDB",  # Назва  бази даних
}

DB_CONFIG_ADMIN2 = {
    "host": "localhost",  # Хост бази даних
    "user": "admin_user",  #Логін до бази даних
    "password": DB_ADMIN_PASSWORD,  #Пароль
    "database": "WarehouseDB",  # Назва  бази даних
}

DB_CONFIG_ADMIN = {
    "host": "localhost",  # Хост бази даних
    "user": "root",  #Логін до бази даних
    "password": "12345678",  #Пароль
    "database": "WarehouseDB",  # Назва  бази даних
}

# Налаштування для підключення до БД
DB_CONFIG = {
    "host": "localhost",  # Хост бази даних
    "user": "root",  #Логін до бази даних
    "password": "12345678",  #Пароль
    "database": "WarehouseDB",  # Назва  бази даних
}

# Налаштування для тимчасових паролів
TEMP_PASSWORD_LENGTH = 8  # довжина тимчасового пароля

#setx DB_AUTH_PASSWORD "MaL#P%.^zeh.u72!"
#setx DB_CHANGE_PASSWORD "<!R&~i,ocda*?F.S#"
#setx DB_ADMIN_PASSWORD "3.%U9Tjr=d=|=[_j"

#echo $env:DB_CHANGE_PASSWORD   # Для PowerShell

