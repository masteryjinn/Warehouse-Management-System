import pymysql
from fastapi import HTTPException
from .database_utils import get_db_connection

def get_orders_function(config, page, limit, search=None, customer_name=None, status_filter=None, min_date=None, max_date=None):
    offset = (page - 1) * limit

    base_query = """
        SELECT 
            o.order_id,
            o.order_date,
            o.status,
            c.name AS customer_name
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
    """

    where_clauses = []
    params = []
    print("min_date =", repr(min_date))
    print("max_date =", repr(max_date))
    if search:
        like_val = f"%{search}%"
        where_clauses.append("(c.name LIKE %s OR o.order_id LIKE %s)")
        params.extend([like_val, like_val])

    if customer_name:
        where_clauses.append("c.name LIKE %s")
        params.append(f"%{customer_name}%")

    if status_filter:
        placeholders = ','.join(['%s'] * len(status_filter))
        where_clauses.append(f"o.status IN ({placeholders})")
        params.extend(status_filter)

    if min_date:
        where_clauses.append("o.order_date >= %s")
        params.append(min_date)

    if max_date:
        where_clauses.append("o.order_date <= %s")
        params.append(max_date)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += """
        ORDER BY o.order_id DESC
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    connection = get_db_connection(config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(base_query, params)
        print("SQL-запит:", base_query)
        print("Параметри:", params)
        return cursor.fetchall()
    except pymysql.MySQLError as err:
        print(f"MySQL error: {err}")
        return []
    finally:
        cursor.close()
        connection.close()

def count_total_orders(config, search=None, customer_name=None, status_filter=None, min_date=None, max_date=None):
    query = """
        SELECT COUNT(DISTINCT o.order_id) AS total
        FROM orders o
        JOIN customers c ON o.customer_id = c.customer_id
    """
    conditions = []
    params = []

    if search:
        like_val = f"%{search}%"
        conditions.append("(c.name LIKE %s OR o.order_id LIKE %s)")
        params.extend([like_val, like_val])

    if customer_name:
        conditions.append("c.name LIKE %s")
        params.append(f"%{customer_name}%")

    if status_filter:
        placeholders = ','.join(['%s'] * len(status_filter))
        conditions.append(f"o.status IN ({placeholders})")
        params.extend(status_filter)

    if min_date:
        conditions.append("o.order_date >= %s")
        params.append(min_date)

    if max_date:
        conditions.append("o.order_date <= %s")
        params.append(max_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        connection.close()

def add_order_to_db(USER_CONFIG, customer_name, date):
    connection = get_db_connection(USER_CONFIG)
    cursor = connection.cursor()

    try:
        # Отримуємо ID клієнта за ім'ям
        cursor.execute("SELECT customer_id FROM Customers WHERE name = %s", (customer_name,))
        result = cursor.fetchone()
        if not result:
            print(f"Клієнта з ім'ям '{customer_name}' не знайдено.")
            return None

        customer_id = result[0]

        # Вставляємо нове замовлення до таблиці Orders
        cursor.execute("""
            INSERT INTO Orders (customer_id, order_date, status)
            VALUES (%s, %s, 'new')
        """, (customer_id, date))

        connection.commit()
        return cursor.lastrowid  # Повертаємо ID нового замовлення

    except pymysql.MySQLError as err:
        raise HTTPException(status_code=500, detail=f"Помилка бази даних: {err}")

    finally:
        cursor.close()
        connection.close()

def delete_orders_from_db(config, order_id):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Перевірка статусу замовлення
        cursor.execute("SELECT status FROM Orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Замовлення не знайдене.")

        status = result[0]
        if status == "shipped":
            raise HTTPException(status_code=400, detail="Виконані замовлення неможливо видалити.")

        # Видалення замовлення
        cursor.execute("""
            DELETE FROM Orders
            WHERE order_id = %s
        """, (order_id,))
        connection.commit()

        return {"message": "Замовлення успішно видалено."}

    except pymysql.MySQLError as err:
        raise HTTPException(status_code=500, detail=f"Помилка бази даних: {err}")

    finally:
        cursor.close()
        connection.close()

def update_order_status_function(config, order_id):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Отримати поточний статус замовлення
        cursor.execute("SELECT status FROM Orders WHERE order_id = %s", (order_id,))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Замовлення не знайдено")

        current_status = result[0]

        # Перевірка наявності товарів у замовленні, якщо статус "new"
        if current_status == "new":
            cursor.execute("SELECT COUNT(*) FROM OrderDetails WHERE order_id = %s", (order_id,))
            details_count = cursor.fetchone()[0]

            if details_count == 0:
                raise HTTPException(status_code=400, detail="Неможливо перейти в статус обробки замовлення, адже воно порожнє")

            new_status = "processing"

        elif current_status == "processing":
            new_status = "shipped"
        elif current_status == "shipped":
            raise HTTPException(status_code=400, detail="Замовлення вже доставлено")
        else:
            raise HTTPException(status_code=400, detail="Невідомий статус")

        # Оновлюємо статус
        cursor.execute("UPDATE Orders SET status = %s WHERE order_id = %s", (new_status, order_id))
        connection.commit()

        return new_status

    except pymysql.MySQLError as err:
        raise HTTPException(status_code=500, detail=f"Помилка бази даних: {err}")

    finally:
        cursor.close()
        connection.close()


def confirm_order_in_db(USER_CONFIG, order_id: int, items: list):
    connection = get_db_connection(USER_CONFIG)
    cursor = connection.cursor()

    try:
        # 1. Оновлюємо статус замовлення
        cursor.execute("""
            UPDATE Orders
            SET status = 'processing'
            WHERE order_id = %s
        """, (order_id,))

        # 2. Додаємо деталі замовлення
        for item in items:
            # Знаходимо section_id за section_name
            cursor.execute("""
                SELECT section_id FROM WarehouseSections
                WHERE name = %s
                LIMIT 1
            """, (item.section,))
            section_result = cursor.fetchone()
            section_id = section_result[0] if section_result else None

            # Додаємо деталі замовлення
            cursor.execute("""
                INSERT INTO OrderDetails (order_id, product_id, quantity, price, section_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                order_id,
                item.product_id,
                item.quantity,
                item.price,
                section_id
            ))

        connection.commit()

    except pymysql.MySQLError as err:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Помилка бази даних: {err}")

    finally:
        cursor.close()
        connection.close()


def get_order_details_from_db(config, order_id):
    query = """
        SELECT 
            od.order_id, 
            p.product_id, 
            p.name AS product_name, 
            p.unit,   
            od.quantity, 
            od.price, 
            ws.name AS section_name
        FROM 
            OrderDetails od
        JOIN Products p ON od.product_id = p.product_id
        JOIN WarehouseSections ws ON od.section_id = ws.section_id
        WHERE od.order_id = %s
    """
    try:
        print(f"[DEBUG] Отримуємо деталі для замовлення ID = {order_id}")
        connection = get_db_connection(config)
        cursor = connection.cursor()
        cursor.execute(query, (order_id,))
        result = cursor.fetchall()
        print(f"[DEBUG] Отримано {len(result)} записів із бази даних")
        return result

    except Exception as err:
        print(f"[ERROR] Помилка при отриманні деталей замовлення: {err}")
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {err}")

    finally:
        cursor.close()
        connection.close()
