import pymysql
from pymysql.cursors import DictCursor
from auth.database_utils import get_db_connection

def add_supplier_to_db(config, name, supplier_type, contacts: dict):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Додаємо клієнта до таблиці suppliers
        cursor.execute("INSERT INTO suppliers (name, type) VALUES (%s, %s)", (name, supplier_type))
        supplier_id = cursor.lastrowid  # Отримуємо ID нового клієнта

        # Додаємо контакти для клієнта
        for contact_type, contact_value in contacts.items():
            if contact_value:
                cursor.execute("""
                    INSERT INTO Contacts_suppliers (supplier_id, contact_type, contact_value)
                    VALUES (%s, %s, %s)
                """, (supplier_id, contact_type, contact_value))

        connection.commit()
        return supplier_id  # Повертаємо ID нового клієнта
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return None
    finally:
        cursor.close()
        connection.close()

def update_supplier_function(config, supplier_id, name, supplier_type, contacts: dict):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Оновлюємо дані постачальника
        print(f"Updating supplier {supplier_id}: name={name}, type={supplier_type}")
        cursor.execute("UPDATE suppliers SET name=%s, type=%s WHERE supplier_id=%s", (name, supplier_type, supplier_id))

        # Оновлюємо або додаємо контакти
        for contact_type, contact_value in contacts.items():
            if contact_value:
                print(f"Updating contact for {contact_type}: {contact_value}")
                
                # Спочатку перевіряємо наявність контакту
                cursor.execute("""
                    SELECT 1 FROM Contacts_suppliers
                    WHERE supplier_id = %s AND contact_type = %s
                """, (supplier_id, contact_type))

                # Якщо запис є (є хоча б один рядок), оновлюємо
                if cursor.fetchone():
                    cursor.execute("""
                        UPDATE Contacts_suppliers
                        SET contact_value = %s
                        WHERE supplier_id = %s AND contact_type = %s
                    """, (contact_value, supplier_id, contact_type))
                else:
                    # Якщо запису нема, додаємо новий
                    cursor.execute("""
                        INSERT INTO Contacts_suppliers (supplier_id, contact_type, contact_value)
                        VALUES (%s, %s, %s)
                    """, (supplier_id, contact_type, contact_value))

        connection.commit()
        return True
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return False
    finally:
        cursor.close()
        connection.close()


def delete_supplier_from_db(config, supplier_id):
    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        # Видаляємо клієнта з таблиці suppliers
        cursor.execute("DELETE FROM suppliers WHERE supplier_id=%s", (supplier_id,))
        connection.commit()
        return True
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return False
    finally:
        cursor.close()
        connection.close()

def get_suppliers_function(config, page, limit, search=None, name_filter=None, type_filter=None, email_required=None, phone_required=None, address_required=None):
    offset = (page - 1) * limit

    base_query = """
        SELECT 
            c.supplier_id, 
            c.name, 
            c.type,
            MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) AS email,
            MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) AS phone,
            MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) AS address
        FROM suppliers c
        LEFT JOIN Contacts_suppliers co ON c.supplier_id = co.supplier_id
    """

    where_clauses = []
    having_clauses = []
    params = []

    if search:
        where_clauses.append("(c.name LIKE %s OR c.type LIKE %s OR co.contact_value LIKE %s)")
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    if name_filter:
        where_clauses.append("c.name LIKE %s")
        params.append(f"%{name_filter}%")

    if type_filter:
        placeholders = ','.join(['%s'] * len(type_filter))
        where_clauses.append(f"c.type IN ({placeholders})")
        params.extend(type_filter)

    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)

    base_query += " GROUP BY c.supplier_id"

    # HAVING для фільтрації агрегованих значень
    if email_required is not None:
        if email_required:
            having_clauses.append("email IS NOT NULL")
        else:
            having_clauses.append("email IS NULL")

    if phone_required is not None:
        if phone_required:
            having_clauses.append("phone IS NOT NULL")
        else:
            having_clauses.append("phone IS NULL")

    if address_required is not None:
        if address_required:
            having_clauses.append("address IS NOT NULL")
        else:
            having_clauses.append("address IS NULL")

    if having_clauses:
        base_query += " HAVING " + " AND ".join(having_clauses)

    base_query += " ORDER BY c.supplier_id LIMIT %s OFFSET %s"
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

def count_total_suppliers(config, search=None, name_filter=None, type_filter=None, email_required=None, phone_required=None, address_required=None):
    query = """
        SELECT COUNT(*) AS total FROM (
            SELECT c.supplier_id,
                MAX(CASE WHEN co.contact_type = 'email' THEN co.contact_value END) AS email,
                MAX(CASE WHEN co.contact_type = 'phone' THEN co.contact_value END) AS phone,
                MAX(CASE WHEN co.contact_type = 'address' THEN co.contact_value END) AS address
            FROM suppliers c
            LEFT JOIN Contacts_suppliers co ON c.supplier_id = co.supplier_id
    """
    where_clauses = []
    having_clauses = []
    params = []

    if search:
        where_clauses.append("(c.name LIKE %s OR c.type LIKE %s OR co.contact_value LIKE %s)")
        like_value = f"%{search}%"
        params.extend([like_value, like_value, like_value])

    if name_filter:
        where_clauses.append("c.name LIKE %s")
        params.append(f"%{name_filter}%")

    if type_filter:
        placeholders = ','.join(['%s'] * len(type_filter))
        where_clauses.append(f"c.type IN ({placeholders})")
        params.extend(type_filter)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " GROUP BY c.supplier_id"

    if email_required is not None:
        if email_required:
            having_clauses.append("email IS NOT NULL")
        else:
            having_clauses.append("email IS NULL")

    if phone_required is not None:
        if phone_required:
            having_clauses.append("phone IS NOT NULL")
        else:
            having_clauses.append("phone IS NULL")

    if address_required is not None:
        if address_required:
            having_clauses.append("address IS NOT NULL")
        else:
            having_clauses.append("address IS NULL")

    if having_clauses:
        query += " HAVING " + " AND ".join(having_clauses)

    query += ") AS subquery"

    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        connection.close()

def get_suppliers_full(config):
    connection = get_db_connection(config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(query = """
            SELECT * 
            FROM Suppliers s
            WHERE EXISTS (
                SELECT 1 FROM Contacts_suppliers cs 
                WHERE cs.supplier_id = s.supplier_id
            )
        """)
        return cursor.fetchall()
    except pymysql.MySQLError as err:
        print(f"Помилка MySQL: {err}")
        return []
    finally:
        cursor.close()
        connection.close()