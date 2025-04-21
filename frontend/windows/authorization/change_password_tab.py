from PyQt6.QtWidgets import QWidget, QFormLayout, QLineEdit, QPushButton, QMessageBox, QCheckBox, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser 
from config.config import API_URL
import re

class ChangePasswordTab(QWidget):
    def __init__(self, auth_window):
        super().__init__()
        self.auth_window = auth_window
        self.setWindowTitle("Зміна пароля")
        self.setStyleSheet("background-color: #e3eaf1; color: #1b263b; font-family: Arial, sans-serif;")
        self.setContentsMargins(10, 10, 10, 10)
        self.setMinimumSize(350, 350)

        # Основний вертикальний макет
        main_layout = QVBoxLayout()

        # Заголовок форми
        title_label = QLabel("Зміна пароля")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; padding: 10px; color: #1e2a38;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Макет для форми
        form_layout = QFormLayout()

        # Стиль для полів вводу
        input_style = """
            background-color: #ffffff; 
            border: 1px solid #415a77; 
            padding: 8px; 
            font-size: 14px; 
            border-radius: 5px;
        """

        # Поля для введення пароля
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet(input_style)

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet(input_style)

        # Чекбокси для відображення паролів
        self.show_new_password_checkbox = QCheckBox('Показати новий пароль')
        self.show_confirm_password_checkbox = QCheckBox('Показати підтвердження пароля')
        
        # Стиль для чекбоксів
        checkbox_style = "font-size: 14px; color: #415a77;"
        self.show_new_password_checkbox.setStyleSheet(checkbox_style)
        self.show_confirm_password_checkbox.setStyleSheet(checkbox_style)

        # Додаємо обробники для чекбоксів
        self.show_new_password_checkbox.stateChanged.connect(self.toggle_new_password_visibility)
        self.show_confirm_password_checkbox.stateChanged.connect(self.toggle_confirm_password_visibility)

        # Стиль для етикеток
        label_style = "font-size: 16px; font-weight: bold; color: #1b263b;"

        # Додаємо рядки до форми
        form_layout.addRow(QLabel("Новий пароль"), self.new_password_input)
        form_layout.addRow(self.show_new_password_checkbox)
        form_layout.addRow(QLabel("Підтвердження пароля"), self.confirm_password_input)
        form_layout.addRow(self.show_confirm_password_checkbox)

        # Кнопка зміни пароля
        change_password_button = QPushButton("Змінити пароль")
        change_password_button.setStyleSheet("""
            QPushButton {
                background-color: #4682b4;
                color: white;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #5a9bd5;
            }
        """)
        change_password_button.clicked.connect(self.change_password)

        # Додаємо віджети в головний макет
        main_layout.addLayout(form_layout)
        main_layout.addWidget(change_password_button)

        self.setLayout(main_layout)

    def toggle_new_password_visibility(self):
        """Перемикає видимість нового пароля"""
        if self.show_new_password_checkbox.isChecked():
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def toggle_confirm_password_visibility(self):
        """Перемикає видимість підтвердження пароля"""
        if self.show_confirm_password_checkbox.isChecked():
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

    def change_password(self):
        """Логіка для зміни пароля з токеном"""
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()

        # Перевірка, чи новий пароль та підтвердження співпадають
        if new_password != confirm_password:
            self.show_error("Новий пароль та підтвердження не співпадають.")
            return

        # Перевірка, чи новий пароль відповідає вимогам
        if not self.is_valid_password(new_password):
            self.show_error("Пароль повинен містити латинські літери, цифру та бути довшим за 7 символів.")
            return

        # Отримуємо поточного користувача
        current_user = CurrentUser()
        token = current_user.get_token()
        is_temp_password = current_user.get_is_temp_password()

        if token is None and is_temp_password==0:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show()
        elif token is None and is_temp_password==1:
            #тут ми після тимчасового паролю
            try:
                # Отримуємо ім'я користувача
                username = current_user.get_name()
                
                # Надсилаємо запит для зміни пароля
                response = requests.post(f"{API_URL}/change-password-after-reset/", 
                                        json={"username": username, "new_password": new_password})
                
                # Перевірка статусу відповіді
                if response.status_code == 400:
                    # Невірні дані
                    error_message = response.json().get("detail", "Невірні дані.")
                
                elif response.status_code == 200:
                    # Пароль успішно змінено
                    QMessageBox.information(self, "Успіх", "Пароль успішно змінено!")
                    # Отримуємо новий токен
                    data = response.json()
                    token = data.get("token")
                    if token:
                        current_user.set_token(token)
                        current_user.password_is_changed()
                    else:
                        error_message = "Не вдалося отримати новий токен."
                        QMessageBox.critical(self, "Помилка", error_message)
                        self.close()
                        self.auth_window.show()
                    self.close()
                    # Очищення полів вводу
                    self.new_password_input.clear()
                    self.confirm_password_input.clear()
                    return
                
                else:
                    # Для всіх інших статусів
                    error_message = f"Невідома помилка. Код: {response.status_code}"
                
                # Виведення помилки
                QMessageBox.critical(self, "Помилка", f"Сталася помилка: {error_message}")
                self.close()
                self.auth_window.show()
            
            except requests.exceptions.RequestException as req_err:
                # Обробка помилки запиту
                QMessageBox.critical(self, "Помилка", f"Помилка запиту: {req_err}")
        elif token and is_temp_password==0:    
            try:
                response = requests.post(
                    f"{API_URL}/change-password/",
                    json={"new_password": new_password},
                    headers={"Authorization": f"Bearer {token}"}
                )

                if response.status_code == 401:
                    error_message = "Токен недійсний або прострочений. Увійдіть у систему знову."
                    self.close()
                    self.auth_window.show()
                elif response.status_code == 400:
                    print("DEBUG 400:", response.json())  # <--- додай це
                    error_message = response.json().get("detail", "Невірні дані.")
                elif response.status_code == 200:
                    self.close()
                    QMessageBox.information(self, "Успіх", "Пароль успішно змінено!")
                    self.new_password_input.clear()
                    self.confirm_password_input.clear()
                    return
                else:
                    error_message = f"Невідома помилка. Код: {response.status_code}"

                QMessageBox.critical(self, "Помилка", f"Сталася помилка: {error_message}")

            except requests.exceptions.RequestException as req_err:
                QMessageBox.critical(self, "Помилка", f"Помилка запиту: {req_err}")

    def is_valid_password(self, password):
        """Перевірка пароля"""
        password_regex = r"^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{7,}$"
        return re.match(password_regex, password) is not None

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)
