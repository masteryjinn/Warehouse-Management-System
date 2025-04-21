from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QComboBox, QHBoxLayout, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from windows.suppliers.supplier_select_dialog import SupplierSelectDialog  # Імпортуйте ваш клас діалогу вибору постачальника
import re
from user_session.current_user import CurrentUser # Імпортуємо модуль для отримання поточного користувача
import requests  # Імпортуємо модуль для роботи з HTTP запитами
from PyQt6.QtWidgets import QDateEdit
from PyQt6.QtCore import QDate


class ProductDialog(QDialog):
    def __init__(self, product=None, api_url=None):
        super().__init__()
        self.product = product
        self.api_url=api_url
        self.categories = None
        self.suppliers = []  # Список постачальників
        self.setWindowTitle("Редагування даних про продукцію" if product else "Додавання даних про продукцію")
        self.setFixedSize(300, 700)
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

    def showEvent(self, event):
        super().showEvent(event)

        self.load_categories()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Назва продукту
        layout.addWidget(QLabel("Назва:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Ціна:"))
        self.price_input = QLineEdit()
        layout.addWidget(self.price_input)

        layout.addWidget(QLabel("Кількість:"))
        self.quantity_input = QLineEdit()
        self.quantity_input.setReadOnly(True)
        self.quantity_input.setText("0")  # Встановлюємо дефолтне значення 0
        layout.addWidget(self.quantity_input)

        layout.addWidget(QLabel("Одиниця виміру:"))
        self.unit_input = QComboBox()
        self.unit_input.addItems(["шт", "кг", "г", "л", "мл", "бокс", "набір"])
        layout.addWidget(self.unit_input)

        layout.addWidget(QLabel("Опис:"))
        self.description_input = QLineEdit()
        layout.addWidget(self.description_input)

        layout.addWidget(QLabel("Категорія:"))
        self.category_input = QComboBox()
        self.category_input.addItems(self.categories)  # передаємо список категорій
        layout.addWidget(self.category_input)

        # Кнопка для вибору постачальника
        self.supplier_button = QPushButton("Вибрати постачальника")
        self.supplier_button.clicked.connect(self.open_supplier_dialog)
        layout.addWidget(self.supplier_button)

        self.supplier_label = QLabel("Постачальник:")
        layout.addWidget(self.supplier_label)

        self.supplier_input = QLineEdit()
        self.supplier_input.setReadOnly(True)  # Поле тільки для перегляду
        layout.addWidget(self.supplier_input)

        self.expiry_checkbox = QCheckBox("Вказати термін придатності")
        self.expiry_checkbox.setChecked(False)
        layout.addWidget(self.expiry_checkbox)

        self.expiry_date_input = QDateEdit()
        self.expiry_date_input.setCalendarPopup(True)
        self.expiry_date_input.setDisplayFormat("dd.MM.yyyy")
        self.expiry_date_input.setEnabled(False)  # спочатку вимкнено

        today = QDate.currentDate()
        self.expiry_date_input.setDate(today)

        layout.addWidget(self.expiry_date_input)


        # Пов’язати чекбокс із вмиканням/вимиканням дати
        self.expiry_checkbox.stateChanged.connect(lambda state: self.expiry_date_input.setEnabled(state == Qt.CheckState.Checked.value))

        # Кнопки для збереження і скасування
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Оновити" if self.product else "Додати")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.save_button.clicked.connect(self.accept_with_validation)
        self.cancel_button.clicked.connect(self.reject)

        if self.product:
            self.populate_fields()

    def load_categories(self):
        current_user = CurrentUser()
        token = current_user.get_token()  # Отримуємо токен користувача
        if not token:
            QMessageBox.warning(self, "Помилка", "Не вдалося отримати токен користувача.")
            return
        try:
            res= requests.get(
                f"{self.api_url}/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            if res.status_code == 200:
                self.categories = res.json().get("categories", [])
            else:
                QMessageBox.warning(self, "Помилка", "Не вдалося отримати категорії.")
        except requests.exceptions.RequestException as req_err:
            print(f"Помилка запиту: {req_err}")
            QMessageBox.warning(self, "Помилка", f"Помилка запиту: {req_err}")

    def open_supplier_dialog(self):
        # Створюємо діалог для вибору постачальника
        dialog = SupplierSelectDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Якщо користувач вибрав постачальника, відображаємо його в полі
            selected_supplier = dialog.get_selected_supplier()
            if selected_supplier:
                self.supplier_input.setText(selected_supplier["name"])

    def populate_fields(self):
        self.name_input.setText(self.product.get("name", ""))
        self.price_input.setText(str(self.product.get("price", "")))
        self.quantity_input.setText(str(self.product.get("quantity", "")))

        unit_value = self.product.get("unit", "")
        if unit_value in [self.unit_input.itemText(i) for i in range(self.unit_input.count())]:
            self.unit_input.setCurrentText(unit_value)
        else:
            self.unit_input.setCurrentText("шт")

        self.description_input.setText(self.product.get("description", ""))
        self.category_input.setCurrentText(self.product.get("category", ""))
        self.supplier_input.setText(self.product.get("supplier_name", ""))

        expiry_str = self.product.get("expiration_date", "")
        if expiry_str:
            year, month, day = map(int, expiry_str.split("-"))
            self.expiry_date_input.setDate(QDate(year, month, day))
            self.expiry_checkbox.setChecked(True)
            self.expiry_date_input.setEnabled(True)
        else:
            self.expiry_checkbox.setChecked(False)
            self.expiry_date_input.setEnabled(False)


    def accept_with_validation(self):
        name = self.name_input.text().strip()
        price = self.price_input.text().strip()
        quantity = self.quantity_input.text().strip()
        unit = self.unit_input.currentText().strip()
        description = self.description_input.text().strip()
        category = self.category_input.currentText().strip()
        supplier = self.supplier_input.text().strip()
        expiry_date = self.expiry_date_input.text().strip()

        # Перевірка на порожні поля
        if not name:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть назву продукту.")
            return

        if not price or not re.match(r'^\d+(\.\d{1,2})?$', price):
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть коректну ціну.")
            return
        
        if not quantity or not re.match(r'^\d+$', quantity):
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть коректну кількість.")
            return
        
        if not unit:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть одиницю виміру.")
            return
        
        if not self.category_input.currentText():
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть категорію.")
            return

        if not supplier:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть постачальника.")
            return
        
        if self.expiry_checkbox.isChecked():
            selected_date = self.expiry_date_input.date()
            tomorrow = QDate.currentDate().addDays(1)
            if selected_date < tomorrow:
                QMessageBox.warning(self, "Помилка", "Термін придатності має бути щонайменше завтрашнім днем.")
                return

        self.accept() 

    def get_data(self):
        return{
            "name": self.name_input.text(),
            "price": float(self.price_input.text()),
            "quantity": int(self.quantity_input.text()),
            "unit": self.unit_input.currentText(),
            "description": self.description_input.text(),
            "category": self.category_input.currentText(),
            "supplier": self.supplier_input.text(),
            "expiry_date": self.expiry_date_input.date().toString("yyyy-MM-dd") if self.expiry_checkbox.isChecked() else None
        }
