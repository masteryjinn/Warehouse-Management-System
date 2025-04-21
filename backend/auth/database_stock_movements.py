import pymysql
from fastapi import HTTPException
from .database_utils import get_db_connection
from pydantic import BaseModel, Field
from typing import List

class IncomingItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)
    unit: str
    section: str

class RelocationItem(BaseModel):
    product_id: int
    quantity: int = Field(ge=0)  # допускаємо 0, бо є ще "номінальне переміщення"
    current_section: str


class RelocationRequest(BaseModel):
    section_id: int
    items: List[RelocationItem]

def relocate_items(config, section_id: int, items: List[RelocationItem]):
    connection = get_db_connection(config)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Перевірка нової секції
            cursor.execute("SELECT section_id, name FROM WarehouseSections WHERE section_id = %s", (section_id,))
            new_section = cursor.fetchone()
            if not new_section:
                raise ValueError(f"Цільову секцію з ID {section_id} не знайдено.")
            new_section_name = new_section["name"]

            for item in items:
                # Перевірка товару
                cursor.execute("SELECT * FROM Products WHERE product_id = %s", (item.product_id,))
                product = cursor.fetchone()
                if not product:
                    raise ValueError(f"Товар з ID {item.product_id} не знайдено.")

                # Перевірка поточної секції
                cursor.execute("SELECT section_id FROM WarehouseSections WHERE name = %s", (item.current_section,))
                current_section = cursor.fetchone()
                if not current_section:
                    raise ValueError(f"Секція '{item.current_section}' не знайдена.")
                current_section_id = current_section["section_id"]

                # Заборона переміщення в ту ж секцію
                if current_section_id == section_id:
                    raise ValueError(f"Неможливо перемістити товар з ID {item.product_id} у ту ж секцію '{new_section_name}'.")

                if item.quantity > 0:
                    # Додаємо записи в StockMovements
                    cursor.execute("""
                        INSERT INTO StockMovements (product_id, quantity, section_id, movement_type, movement_reason)
                        VALUES (%s, %s, %s, 'out', 'переміщення між секціями')
                    """, (item.product_id, item.quantity, current_section_id))

                    cursor.execute("""
                        INSERT INTO StockMovements (product_id, quantity, section_id, movement_type, movement_reason)
                        VALUES (%s, %s, %s, 'in', 'переміщення між секціями')
                    """, (item.product_id, item.quantity, section_id))

                cursor.execute("""
                        UPDATE Products
                        SET section_id = %s
                        WHERE product_id = %s
                    """, (section_id, item.product_id))

        connection.commit()
    finally:
        connection.close()



def add_income_items_to_db(config, items: List[IncomingItem]):
    connection = get_db_connection(config)
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            for item in items:
                # Перевірка, чи існує товар
                cursor.execute("SELECT * FROM Products WHERE product_id = %s", (item.product_id,))
                product = cursor.fetchone()
                if not product:
                    raise ValueError(f"Товар з ID {item.product_id} не знайдено.")

                # Перевірка секції
                cursor.execute("SELECT section_id FROM WarehouseSections WHERE name = %s", (item.section,))
                section = cursor.fetchone()
                if not section:
                    raise ValueError(f"Секція '{item.section}' не знайдена.")

                # Вставка руху товару
                cursor.execute("""
                    INSERT INTO StockMovements (product_id, quantity, section_id, movement_type, movement_reason)
                    VALUES (%s, %s, %s, %s, 'Надходження товару')
                """, (item.product_id, item.quantity, section["section_id"], "in"))

                cursor.execute("""
                    UPDATE Products
                    SET quantity = quantity + %s
                    WHERE product_id = %s
                """, (item.quantity, item.product_id))

        connection.commit()
    finally:
        connection.close()


def get_stock_movements(config, page, limit, movement_type=None, product_id=None, section_id=None,
                        date_from=None, date_to=None, quantity_min=None, quantity_max=None):
    offset = (page - 1) * limit

    query = """
        SELECT 
            sm.movement_id,
            p.name AS product_name,
            sm.movement_type,
            sm.quantity,
            sm.movement_date,
            sm.movement_reason,
            ws.name AS section_name
        FROM StockMovements sm
        LEFT JOIN Products p ON sm.product_id = p.product_id
        LEFT JOIN WarehouseSections ws ON sm.section_id = ws.section_id
    """

    where_clauses = []
    params = []

    if movement_type:
        where_clauses.append("sm.movement_type = %s")
        params.append(movement_type)

    if product_id:
        where_clauses.append("sm.product_id = %s")
        params.append(product_id)

    if section_id:
        where_clauses.append("sm.section_id = %s")
        params.append(section_id)

    if date_from:
        where_clauses.append("sm.movement_date >= %s")
        params.append(date_from)

    if date_to:
        where_clauses.append("sm.movement_date <= %s")
        params.append(date_to)

    if quantity_min is not None:
        where_clauses.append("sm.quantity >= %s")
        params.append(quantity_min)

    if quantity_max is not None:
        where_clauses.append("sm.quantity <= %s")
        params.append(quantity_max)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    query += " ORDER BY sm.movement_date DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    connection = get_db_connection(config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    try:
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()

def count_stock_movements(config, movement_type=None, product_id=None, section_id=None,
                          date_from=None, date_to=None, quantity_min=None, quantity_max=None):
    query = """
        SELECT COUNT(*) as total
        FROM StockMovements sm
        LEFT JOIN Products p ON sm.product_id = p.product_id
        LEFT JOIN WarehouseSections ws ON sm.section_id = ws.section_id
    """

    where_clauses = []
    params = []

    if movement_type:
        where_clauses.append("sm.movement_type = %s")
        params.append(movement_type)

    if product_id:
        where_clauses.append("sm.product_id = %s")
        params.append(product_id)

    if section_id:
        where_clauses.append("sm.section_id = %s")
        params.append(section_id)

    if date_from:
        where_clauses.append("sm.movement_date >= %s")
        params.append(date_from)

    if date_to:
        where_clauses.append("sm.movement_date <= %s")
        params.append(date_to)

    if quantity_min is not None:
        where_clauses.append("sm.quantity >= %s")
        params.append(quantity_min)

    if quantity_max is not None:
        where_clauses.append("sm.quantity <= %s")
        params.append(quantity_max)

    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)

    connection = get_db_connection(config)
    cursor = connection.cursor()

    try:
        cursor.execute(query, params)
        result = cursor.fetchone()
        return result[0] if result else 0
    finally:
        cursor.close()
        connection.close()
