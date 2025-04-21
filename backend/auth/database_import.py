import pymysql
from fastapi import HTTPException
from .database_utils import get_db_connection

def insert_employees(config, data):
    with get_db_connection(config) as conn:
        with conn.cursor() as cursor:
            for item in data:
                cursor.execute("""
                    INSERT INTO Employees (name, position) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE position = VALUES(position)
                """, (item['name'], item.get('position', None)))
        conn.commit()

def insert_customers(config, data):
    with get_db_connection(config) as conn:
        with conn.cursor() as cursor:
            for item in data:
                cursor.execute("""
                    INSERT INTO Customers (name, type) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE type = VALUES(type)
                """, (item['name'], item['type']))
        conn.commit()

def insert_suppliers(config, data):
    with get_db_connection(config) as conn:
        with conn.cursor() as cursor:
            for item in data:
                cursor.execute("""
                    INSERT INTO Suppliers (name, type) 
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE type = VALUES(type)
                """, (item['name'], item['type']))
        conn.commit()
