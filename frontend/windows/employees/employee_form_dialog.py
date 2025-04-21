from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QMessageBox
)
import re

class EmployeeFormDialog(QDialog):
    def __init__(self, parent=None, employee_data=None):
        super().__init__(parent)
        self.setWindowTitle("Форма співробітника")
        self.setMinimumSize(400, 270)

        self.setStyleSheet("""
            QWidget {
                background-color: #2F3A53;
                color: white;
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
            }
            QLabel {
                font-size: 14pt;
                margin-bottom: 5px;
            }
            QLineEdit {
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

        self.layout = QFormLayout()
        self.setLayout(self.layout)

        self.name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.email_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QLineEdit()

        self.layout.addRow("Ім’я:", self.name_input)
        self.layout.addRow("Посада:", self.position_input)
        self.layout.addRow("Email:", self.email_input)
        self.layout.addRow("Телефон:", self.phone_input)
        self.layout.addRow("Адреса:", self.address_input)

        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Оновити" if employee_data else "Зберегти")
        self.cancel_btn = QPushButton("Скасувати")
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        self.layout.addRow(button_layout)

        self.save_btn.clicked.connect(self.validate_and_accept)
        self.cancel_btn.clicked.connect(self.reject)

        if employee_data:
            self.name_input.setText(employee_data.get("name", ""))
            self.position_input.setText(employee_data.get("position", ""))
            self.email_input.setText(employee_data.get("email", ""))
            self.phone_input.setText(employee_data.get("phone", ""))
            self.address_input.setText(employee_data.get("address", ""))
        else:
            self.clear_fields()

    def clear_fields(self):
        self.name_input.clear()
        self.position_input.clear()
        self.email_input.clear()
        self.phone_input.clear()
        self.address_input.clear()

    def validate_and_accept(self):
        name = self.name_input.text().strip()
        position = self.position_input.text().strip()
        email = self.email_input.text().strip()
        raw_phone = self.phone_input.text().strip()

        if not name or not position or not email:
            QMessageBox.warning(self, "Помилка", "Будь ласка, заповніть обов'язкові поля: Ім’я, Посада, Email.")
            return

        if not self.validate_email(email):
            QMessageBox.warning(self, "Помилка", "Введено некоректний email.")
            return

        cleaned_phone = re.sub(r'[^\d+]', '', raw_phone)

        # Перевірка: + і 9–15 цифр
        if cleaned_phone and not re.match(r'^\+?\d{9,15}$', cleaned_phone):
            QMessageBox.warning(self, "Помилка", "Невірний формат телефону. Має містити 9-15 цифр.")
            return
        
        # Оновлення поля телефону очищеним значенням
        self.phone_input.setText(cleaned_phone)


        self.accept()

    def validate_email(self, email: str) -> bool:
        pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(pattern, email) is not None

    def validate_phone(self, phone: str) -> bool:
        clean_phone = re.sub(r"[^\d]", "", phone)
        return len(clean_phone) >= 9

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "position": self.position_input.text(),
            "email": self.email_input.text(),
            "phone": self.phone_input.text(),
            "address": self.address_input.text(),
        }
