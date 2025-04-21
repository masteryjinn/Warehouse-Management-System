import pymysql
from auth.database_utils import get_db_connection

def add_customer_to_db(config, name, customer_type, contacts: dict):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Додаємо клієнта до таблиці Customers
        cursor.execute("INSERT INTO Customers (name, type) VALUES (%s, %s)", (name, customer_type))
        customer_id = cursor.lastrowid  # Отримуємо ID нового клієнта

        # Додаємо контакти для клієнта
        for contact_type, contact_value in contacts.items():
            if contact_value:
                cursor.execute("""
                    INSERT INTO Contacts_customers (customer_id, contact_type, contact_value)
                    VALUES (%s, %s, %s)
                """, (customer_id, contact_type, contact_value))

        connection.commit()
        return customer_id  # Повертаємо ID нового клієнта
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return None
    finally:
        cursor.close()
        connection.close()

def update_customer_function(config, customer_id, name, customer_type, contacts: dict):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Оновлюємо дані постачальника
        print(f"Updating Customers {customer_id}: name={name}, type={customer_type}")
        cursor.execute("UPDATE Customers SET name=%s, type=%s WHERE customer_id=%s", (name, customer_type, customer_id))

        # Оновлюємо або додаємо контакти
        for contact_type, contact_value in contacts.items():
            if contact_value:
                print(f"Updating contact for {contact_type}: {contact_value}")
                
                # Спочатку перевіряємо наявність контакту
                cursor.execute("""
                    SELECT 1 FROM Contacts_customers
                    WHERE customer_id = %s AND contact_type = %s
                """, (customer_id, contact_type))

                # Якщо запис є (є хоча б один рядок), оновлюємо
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE Contacts_customers
                        SET contact_value = %s
                        WHERE customer_id = %s AND contact_type = %s
                    """, (contact_value, customer_id, contact_type))
                else:
                    # Якщо запису нема, додаємо новий
                    cursor.execute("""
                        INSERT INTO Contacts_customers (customer_id, contact_type, contact_value)
                        VALUES (%s, %s, %s)
                    """, (customer_id, contact_type, contact_value))

        connection.commit()
        return True
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return False
    finally:
        cursor.close()
        connection.close()

def delete_customer_from_db(config, customer_id):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Перевіряємо, чи є незавершені замовлення
        check_query = """
            SELECT COUNT(*) FROM Orders 
            WHERE customer_id = %s AND status IN ('new', 'processing')
        """
        cursor.execute(check_query, (customer_id,))
        (active_orders_count,) = cursor.fetchone()

        if active_orders_count > 0:
            print("Клієнта не можна видалити: є незавершені замовлення.")
            return False

        # Якщо немає незавершених замовлень — видаляємо клієнта
        cursor.execute("DELETE FROM Customers WHERE customer_id = %s", (customer_id,))
        connection.commit()
        return cursor.rowcount > 0

    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return False
    finally:
        cursor.close()
        connection.close()


def get_customers_function(config, page, limit, search=None, name_filter=None, type_filter=None, email_required=None, phone_required=None, address_required=None):
    offset = (page - 1) * limit

    base_query = """
        SELECT 
            c.customer_id, 
            c.name, 
            c.type,
            MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) AS email,
            MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) AS phone,
            MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) AS address
        FROM Customers c
        LEFT JOIN Contacts_customers co ON c.customer_id = co.customer_id
    """

    where_clauses = []
    having_clauses = []
    params = []
    having_params = []

    if search:
        where_clauses.append("(c.name LIKE %s OR c.type LIKE %s OR co.contact_value LIKE %s)")
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    if name_filter:
        where_clauses.append("(c.name LIKE %s)")
        like_value = f"%{name_filter}%"
        params.append(like_value)

    if type_filter:
        where_clauses.append("c.type = %s")
        params.append(type_filter)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += """
        GROUP BY c.customer_id
    """

    # Тепер додаємо HAVING умови до агрегованих значень
    if email_required is not None:
        if email_required:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) IS NOT NULL")
        else:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) IS NULL")

    if phone_required is not None:
        if phone_required:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) IS NOT NULL")
        else:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) IS NULL")

    if address_required is not None:
        if address_required:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) IS NOT NULL")
        else:
            having_clauses.append("MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) IS NULL")

    if having_clauses:
        base_query += " HAVING " + " AND ".join(having_clauses)

    base_query += """
        ORDER BY c.customer_id
        LIMIT %s OFFSET %s
    """
    params.extend([limit, offset])

    connection = get_db_connection(config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(base_query, params)
        return cursor.fetchall()
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return []
    finally:
        cursor.close()
        connection.close()


def count_total_customers(config, search=None, name_filter=None, type_filter=None, email_required=None, phone_required=None, address_required=None):
    subquery = """
        SELECT 
            c.customer_id, 
            c.name, 
            c.type,
            MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) AS email,
            MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) AS phone,
            MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) AS address
        FROM Customers c
        LEFT JOIN Contacts_customers co ON c.customer_id = co.customer_id
    """

    conditions = []
    params = []

    if search:
        conditions.append("(c.name LIKE %s OR c.type LIKE %s OR co.contact_value LIKE %s)")
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    if name_filter:
        conditions.append("c.name LIKE %s")
        like_value = f"%{name_filter}%"
        params.append(like_value)

    if type_filter:
        conditions.append("c.type = %s")
        params.append(type_filter)

    if conditions:
        subquery += " WHERE " + " AND ".join(conditions)

    subquery += " GROUP BY c.customer_id"

    full_query = f"""
        SELECT COUNT(*) AS total FROM (
            {subquery}
        ) AS sub
        WHERE 1=1
    """

    # Після агрегації – фільтруємо по email/phone/address
    if email_required is not None:
        if email_required:
            full_query += " AND email IS NOT NULL"
        else:
            full_query += " AND email IS NULL"

    if phone_required is not None:
        if phone_required:
            full_query += " AND phone IS NOT NULL"
        else:
            full_query += " AND phone IS NULL"

    if address_required is not None:
        if address_required:
            full_query += " AND address IS NOT NULL"
        else:
            full_query += " AND address IS NULL"

    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        cursor.execute(full_query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        connection.close()


def get_customers_full(config):
    connection = get_db_connection(config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        query = """
            SELECT * 
            FROM Customers c
            WHERE EXISTS (
                SELECT 1 FROM Contacts_customers cc 
                WHERE cc.customer_id = c.customer_id
            )
        """
        cursor.execute(query)
        return cursor.fetchall()
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return []
    finally:
        cursor.close()
        connection.close()
