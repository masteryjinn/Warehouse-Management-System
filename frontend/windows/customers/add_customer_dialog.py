from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QComboBox, QHBoxLayout, QMessageBox
)
import re

class CustomerDialog(QDialog):
    def __init__(self, customer=None):
        super().__init__()
        self.customer = customer
        self.setWindowTitle("Редагування клієнта" if customer else "Додавання клієнта")
        self.setFixedSize(300, 500)
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
            QComboBox {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 10px;
                color: white;
                font-size: 12pt;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Назва клієнта
        layout.addWidget(QLabel("Ім’я клієнта:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Тип клієнта
        layout.addWidget(QLabel("Тип клієнта:"))
        self.type_input = QComboBox()
        self.type_dict = {
            "Фізична особа": "individual",
            "Юридична особа": "business"
        }
        self.type_input.addItems(self.type_dict.keys())
        layout.addWidget(self.type_input)

        # Телефон
        layout.addWidget(QLabel("Телефон:"))
        self.phone_input = QLineEdit()
        layout.addWidget(self.phone_input)

        # Email
        layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        layout.addWidget(self.email_input)

        # Адреса
        layout.addWidget(QLabel("Адреса:"))
        self.address_input = QLineEdit()
        layout.addWidget(self.address_input)

        # Кнопки
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Оновити" if self.customer else "Додати")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.save_button.clicked.connect(self.accept_with_validation)
        self.cancel_button.clicked.connect(self.reject)

        if self.customer:
            self.populate_fields()

    def populate_fields(self):
        self.name_input.setText(self.customer.get("name", ""))
        # Встановлюємо текст на основі англійського значення
        type_ukrainian = self.customer.get("type", "individual")
        self.type_input.setCurrentText(self.get_ukrainian_type(type_ukrainian))
        self.phone_input.setText(self.customer.get("phone", ""))
        self.email_input.setText(self.customer.get("email", ""))
        self.address_input.setText(self.customer.get("address", ""))

    def accept_with_validation(self):
        name = self.name_input.text().strip()
        raw_phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()
        address = self.address_input.text().strip()

        # Ім’я (обов’язково)
        if not name:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть ім’я клієнта.")
            return

        cleaned_phone = re.sub(r'[^\d+]', '', raw_phone)

        # Перевірка: + і 9–15 цифр
        if cleaned_phone and not re.match(r'^\+?\d{9,15}$', cleaned_phone):
            QMessageBox.warning(self, "Помилка", "Невірний формат телефону. Має містити 9-15 цифр.")
            return
        
        # Оновлення поля телефону очищеним значенням
        self.phone_input.setText(cleaned_phone)

        # Email (опціонально, але якщо вказано — перевіряємо формат)
        if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', email):
            QMessageBox.warning(self, "Помилка", "Невірний формат email.")
            return

        # Адреса (опціонально — взагалі не перевіряємо)

        self.accept()  # Усе добре — приймаємо форму



    def get_data(self):
        # Повертаємо англійське значення типу
        type_ukrainian = self.type_input.currentText()
        type_english = self.type_dict.get(type_ukrainian, "individual")
        return {
            "name": self.name_input.text(),
            "type": type_english,
            "phone": self.phone_input.text(),
            "email": self.email_input.text(),
            "address": self.address_input.text()
        }

    def get_ukrainian_type(self, type_english):
        # Повертаємо українське значення для англійського типу
        for ukrainian, english in self.type_dict.items():
            if english == type_english:
                return ukrainian
        return "Фізична особа"  # За замовчуванням
