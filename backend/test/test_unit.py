import unittest
import pymysql
from auth.database_employees import register_user_in_db
from auth.database_utils import get_db_connection  # імпортуємо функцію з модуля
from unittest.mock import patch

class TestUserRegistration(unittest.TestCase):
    
    @patch('your_module.get_db_connection')
    def test_register_user_in_db(self, mock_get_db_connection):
        # Створюємо мок-підключення
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        
        # Припускаємо, що функція для виконання запитів повертає успішний результат
        mock_cursor.execute.return_value = None
        
        username = 'test_user'
        password_hash = 'hashed_password'
        role = 'admin'
        
        # Викликаємо функцію реєстрації користувача
        result = register_user_in_db(username, password_hash, role)
        
        # Перевірка, чи повертає функція True
        self.assertTrue(result)
        
        # Перевірка, чи був виконаний SQL-запит для створення користувача
        mock_cursor.execute.assert_any_call(f"CREATE USER '{username}'@'localhost' IDENTIFIED BY '{password_hash}'")
        
        # Перевірка, чи було надано відповідні ролі користувачу
        if role == 'admin':
            mock_cursor.execute.assert_any_call("GRANT 'admin_role' TO %s@'localhost'", (username,))
            mock_cursor.execute.assert_any_call("SET DEFAULT ROLE 'admin_role' TO %s@'localhost'", (username,))
        elif role == 'manager':
            mock_cursor.execute.assert_any_call("GRANT 'manager_role' TO %s@'localhost'", (username,))
            mock_cursor.execute.assert_any_call("SET DEFAULT ROLE 'manager_role' TO %s@'localhost'", (username,))
        elif role == 'employee':
            mock_cursor.execute.assert_any_call("GRANT 'employee_role' TO %s@'localhost'", (username,))
            mock_cursor.execute.assert_any_call("SET DEFAULT ROLE 'employee_role' TO %s@'localhost'", (username,))
        
        # Перевірка, чи були виконані commit та закриття з'єднання
        mock_connection.commit.assert_called_once()
        mock_connection.close.assert_called_once()

    @patch('your_module.get_db_connection')
    def test_register_user_in_db_error(self, mock_get_db_connection):
        # Створюємо мок-підключення
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value
        
        # Налаштовуємо виключення, яке може статися при виконанні запиту
        mock_cursor.execute.side_effect = pymysql.MySQLError("Database error")
        
        username = 'test_user'
        password_hash = 'hashed_password'
        role = 'admin'
        
        # Викликаємо функцію реєстрації користувача, яка повинна повернути False при помилці
        result = register_user_in_db(username, password_hash, role)
        
        # Перевірка, чи функція повернула False у разі помилки
        self.assertFalse(result)

        # Перевірка, чи був викликаний rollback у разі помилки
        mock_connection.rollback.assert_called_once()
        
        # Перевірка, чи було закрите з'єднання
        mock_connection.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
