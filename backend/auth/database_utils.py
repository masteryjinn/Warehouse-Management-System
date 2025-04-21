import pymysql
# Функція для підключення до бази даних
def get_db_connection(config):
    return pymysql.connect(**config, autocommit=True)  # Додаємо autocommit=True


