from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QPushButton, QVBoxLayout, QComboBox, QMessageBox, QLabel
)
from PyQt6.QtCore import Qt
import requests
import re
from user_session.current_user import CurrentUser

class RegisterEmployeeWindow(QDialog):
    def __init__(self, emp_id, api_url, parent=None):
        super().__init__(parent)
        self.emp_id = emp_id
        self.api_url = api_url
        self.setWindowTitle("Реєстрація користувача")

        self.setStyleSheet("""
            QWidget {
                background-color: #2F3A53;
                color: white;
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
            }
            QLineEdit {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 5px;
                color: white;
            }
            QLineEdit[valid="false"] {
                border: 2px solid red;
            }
            QLineEdit[valid="true"] {
                border: 2px solid green;
            }
            QLabel.hint {
                font-size: 10pt;
                color: #FFA07A;
                margin-left: 5px;
                margin-bottom: 10px;
            }
            QComboBox {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 5px;
                color: white;
            }
            QPushButton {
                background-color: #557A95;
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #4A6581;
            }
        """)

        self.username_field = QLineEdit(self)
        self.username_field.setPlaceholderText("Ім’я користувача")

        self.password_field = QLineEdit(self)
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setPlaceholderText("Пароль")
        self.password_hint = QLabel(self)
        self.password_hint.setObjectName("password_hint")
        self.password_hint.setProperty("class", "hint")

        self.confirm_password_field = QLineEdit(self)
        self.confirm_password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_field.setPlaceholderText("Підтвердження пароля")
        self.confirm_hint = QLabel(self)
        self.confirm_hint.setObjectName("confirm_hint")
        self.confirm_hint.setProperty("class", "hint")

        self.role_combo = QComboBox(self)
        self.role_combo.addItems(["Адмін", "Менеджер", "Звичайний працівник"])

        self.toggle_button = QPushButton("Показати/Сховати пароль", self)
        self.toggle_button.clicked.connect(self.toggle_password_visibility)

        self.register_button = QPushButton("Зареєструвати", self)
        self.register_button.clicked.connect(self.register_user)

        layout = QVBoxLayout(self)
        layout.addWidget(self.username_field)
        layout.addWidget(self.password_field)
        layout.addWidget(self.password_hint)
        layout.addWidget(self.confirm_password_field)
        layout.addWidget(self.confirm_hint)
        layout.addWidget(self.role_combo)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.register_button)

        self.setLayout(layout)

        # Підключення до сигналів змін
        self.password_field.textChanged.connect(self.validate_password_live)
        self.confirm_password_field.textChanged.connect(self.validate_confirm_password)

    def toggle_password_visibility(self):
        mode = QLineEdit.EchoMode.Normal if self.password_field.echoMode() == QLineEdit.EchoMode.Password else QLineEdit.EchoMode.Password
        self.password_field.setEchoMode(mode)
        self.confirm_password_field.setEchoMode(mode)

    def validate_password_live(self):
        password = self.password_field.text()
        if self.validate_password(password):
            self.password_hint.setText("✔ Надійний пароль")
            self.password_field.setProperty("valid", True)
        else:
            self.password_hint.setText("✘ Пароль має містити щонайменше 8 символів, цифри та букви.")
            self.password_field.setProperty("valid", False)
        self.password_field.style().unpolish(self.password_field)
        self.password_field.style().polish(self.password_field)
        self.validate_confirm_password()  # перевірка підтвердження одразу

    def validate_confirm_password(self):
        password = self.password_field.text()
        confirm = self.confirm_password_field.text()
        if password == confirm and confirm != "":
            self.confirm_hint.setText("✔ Паролі збігаються")
            self.confirm_password_field.setProperty("valid", True)
        else:
            self.confirm_hint.setText("✘ Паролі не збігаються")
            self.confirm_password_field.setProperty("valid", False)
        self.confirm_password_field.style().unpolish(self.confirm_password_field)
        self.confirm_password_field.style().polish(self.confirm_password_field)

    def validate_password(self, password: str) -> bool:
        return (
            len(password) >= 8 and
            re.search(r"[A-Za-z]", password) and
            re.search(r"\d", password)
        )

    def register_user(self):
        username = self.username_field.text()
        password = self.password_field.text()
        confirm_password = self.confirm_password_field.text()
        selected_role = self.role_combo.currentText()

        role_map = {
            "Адмін": "admin",
            "Менеджер": "manager",
            "Звичайний працівник": "employee"
        }
        role = role_map.get(selected_role)

        if not username or not password or not confirm_password:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть всі поля.")
            return

        if not self.validate_password(password):
            QMessageBox.warning(self, "Помилка", "Пароль не відповідає вимогам.")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "Помилка", "Паролі не збігаються.")
            return

        try:
            current_user = CurrentUser()
            token = current_user.get_token()
            if token is None:
                QMessageBox.critical(self, "Помилка", "Не вдалося отримати токен авторизації.")
                return

            res = requests.post(
                f"{self.api_url}/register/{self.emp_id}",
                json={"username": username, "password": password, "role": role},
                headers={"Authorization": f"Bearer {token}"}
            )

            if res.status_code == 400:
                QMessageBox.warning(self, "Помилка", "Користувач з таким ім'ям вже існує.")
            elif res.status_code == 403:
                QMessageBox.critical(self, "Помилка", "У вас немає прав для реєстрації користувача.")
            elif res.status_code != 200:
                raise Exception(f"Сталася помилка: {res.status_code}")
            else:
                QMessageBox.information(self, "Готово", "Користувача зареєстровано")
                self.accept()

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Реєстрація не вдалася: {e}")
            self.reject()

        finally:
            self.username_field.clear()
            self.password_field.clear()
            self.confirm_password_field.clear()
            self.role_combo.setCurrentIndex(0)
            self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_hint.clear()
            self.confirm_hint.clear()
