from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton, QHBoxLayout, QDateEdit
)
from PyQt6.QtCore import QDate
import requests
from user_session.current_user import CurrentUser
from PyQt6.QtWidgets import QSpinBox
from windows.stock_movements.add_incoming_dialog import ProductSearchDialog
from PyQt6.QtWidgets import QCheckBox
from PyQt6.QtWidgets import QMessageBox


class StockMovementFilterDialog(QDialog):
    def __init__(self, parent=None, current_filters=None):
        super().__init__(parent)
        self.setWindowTitle("Фільтр руху товарів")
        self.setFixedSize(350, 750)
        self.current_filters = current_filters or {}
        self.products = []
        self.sections = []

        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_options()

    def init_ui(self):
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
        layout = QVBoxLayout(self)

        self.movement_type_combo = QComboBox()
        self.movement_type_combo.addItems(["", "in", "out"])

        self.product_combo = QComboBox()
        self.product_search_button = QPushButton("Пошук...")
        self.product_search_button.clicked.connect(self.open_product_search)

        product_layout = QHBoxLayout()
        product_layout.addWidget(self.product_combo)
        product_layout.addWidget(self.product_search_button)

        layout.addWidget(QLabel("Продукт:"))
        layout.addLayout(product_layout)

        self.section_combo = QComboBox()

        # Чекбокси
        self.use_date_filter_checkbox = QCheckBox("Фільтрувати за датою")
        self.use_quantity_filter_checkbox = QCheckBox("Фільтрувати за кількістю")
        self.use_date_filter_checkbox.setChecked(False)
        self.use_quantity_filter_checkbox.setChecked(False)

        # Дата
        self.date_from = QDateEdit(calendarPopup=True)
        self.date_from.setDate(QDate.currentDate())
        self.date_to = QDateEdit(calendarPopup=True)
        self.date_to.setDate(QDate.currentDate().addDays(1))

        # Кількість
        self.quantity_min_spin = QSpinBox()
        self.quantity_min_spin.setMinimum(0)
        self.quantity_min_spin.setMaximum(100000)
        self.quantity_min_spin.setPrefix("від: ")

        self.quantity_max_spin = QSpinBox()
        self.quantity_max_spin.setMinimum(0)
        self.quantity_max_spin.setMaximum(100000)
        self.quantity_max_spin.setPrefix("до: ")

        # Додаємо до layout
        layout.addWidget(self.use_date_filter_checkbox)
        layout.addWidget(QLabel("Дата від:"))
        layout.addWidget(self.date_from)
        layout.addWidget(QLabel("Дата до:"))
        layout.addWidget(self.date_to)

        layout.addWidget(self.use_quantity_filter_checkbox)
        layout.addWidget(QLabel("Кількість:"))
        layout.addWidget(self.quantity_min_spin)
        layout.addWidget(self.quantity_max_spin)

        layout.addWidget(QLabel("Тип руху:"))
        layout.addWidget(self.movement_type_combo)
        layout.addWidget(QLabel("Секція:"))
        layout.addWidget(self.section_combo)


        button_layout = QVBoxLayout()
        self.apply_button = QPushButton("Застосувати")
        self.clear_button = QPushButton("Очистити")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.apply_button.clicked.connect(self.validate_and_accept)
        self.clear_button.clicked.connect(self.clear_fields)
        self.cancel_button.clicked.connect(self.reject)
        self.use_date_filter_checkbox.stateChanged.connect(self.toggle_date_fields)
        self.use_quantity_filter_checkbox.stateChanged.connect(self.toggle_quantity_fields)
        # Після створення елементів у init_ui:
        self.toggle_date_fields(self.use_date_filter_checkbox.checkState())
        self.toggle_quantity_fields(self.use_quantity_filter_checkbox.checkState())


    def load_options(self):
        current_user = CurrentUser()
        token = current_user.get_token()

        try:
            sections_res = requests.get("http://localhost:8000/sections/full", headers={"Authorization": f"Bearer {token}"})

            if sections_res.status_code == 200:
                self.sections = sections_res.json().get("sections", [])
                self.section_combo.addItem("")
                for section in self.sections:
                    self.section_combo.addItem(section["name"], section["section_id"])
                self.section_combo.addItem("Пакувальна секція", 19)
        except requests.RequestException as e:
            print(f"Помилка при завантаженні опцій: {e}")

        self.load_current_filters()

            
    def toggle_date_fields(self, state):
        enabled = state == 2
        self.date_from.setEnabled(enabled)
        self.date_to.setEnabled(enabled)

    def toggle_quantity_fields(self, state):
        enabled = state == 2
        self.quantity_min_spin.setEnabled(enabled)
        self.quantity_max_spin.setEnabled(enabled)


    def open_product_search(self):
        dialog = ProductSearchDialog(self)
        if dialog.exec():
            selected_product = dialog.selected_product
            if selected_product:
                product_name = selected_product["name"]
                product_id = selected_product["product_id"]

                # Перевіряємо, чи вже є такий продукт у comboBox
                index = self.product_combo.findData(product_id)
                if index == -1:
                    self.product_combo.addItem(product_name, product_id)
                    index = self.product_combo.findData(product_id)
                self.product_combo.setCurrentIndex(index)


    def get_filters(self):
        filters = {}

        movement_type = self.movement_type_combo.currentText()
        if movement_type:
            filters["movement_type"] = movement_type

        product_id = self.product_combo.currentData()
        if product_id:
            filters["product_id"] = product_id

        section_index = self.section_combo.currentIndex()
        if section_index > 0:
            filters["section_id"] = self.section_combo.itemData(section_index)

        if self.use_date_filter_checkbox.isChecked():
            filters["date_from"] = self.date_from.date().toString("yyyy-MM-dd")
            filters["date_to"] = self.date_to.date().toString("yyyy-MM-dd")

        if self.use_quantity_filter_checkbox.isChecked():
            if self.quantity_min_spin.value() > 0:
                filters["quantity_min"] = self.quantity_min_spin.value()
            if self.quantity_max_spin.value() > 0 and self.quantity_max_spin.value()>=self.quantity_min_spin.value():
                filters["quantity_max"] = self.quantity_max_spin.value()

        return filters

    def validate_and_accept(self):
        if self.use_date_filter_checkbox.isChecked():
            date_from = self.date_from.date()
            date_to = self.date_to.date()
            if date_from > date_to:
                QMessageBox.warning(self, "Помилка", "Дата 'від' не може бути пізніше за дату 'до'.")
                return
            if date_from.daysTo(date_to) < 1:
                QMessageBox.warning(self, "Помилка", "Різниця між датами має бути хоча б 1 день.")
                return

        if self.use_quantity_filter_checkbox.isChecked():
            q_min = self.quantity_min_spin.value()
            q_max = self.quantity_max_spin.value()
            if q_min > q_max and q_max > 0:
                QMessageBox.warning(self, "Помилка", "Мінімальна кількість не може перевищувати максимальну.")
                return
            if q_max - q_min < 1 and q_max > 0:
                QMessageBox.warning(self, "Помилка", "Різниця між мінімальною та максимальною кількістю має бути хоча б 1.")
                return

        self.accept()


    def load_current_filters(self):
        if not self.current_filters:
            return

        movement_type = self.current_filters.get("movement_type", "")
        index = self.movement_type_combo.findText(movement_type)
        if index >= 0:
            self.movement_type_combo.setCurrentIndex(index)

        product_id = self.current_filters.get("product_id")
        if product_id:
            index = self.product_combo.findData(product_id)
            if index == -1:
                try:
                    product_res = requests.get(f"http://localhost:8000/products/{product_id}", headers={"Authorization": f"Bearer {CurrentUser().get_token()}"})
                    if product_res.status_code == 200:
                        product = product_res.json()
                        self.product_combo.addItem(product["name"], product["product_id"])
                        index = self.product_combo.findData(product_id)
                        self.product_combo.setCurrentIndex(index)
                except requests.RequestException as e:
                    print(f"Помилка при завантаженні продукту: {e}")

        section_id = self.current_filters.get("section_id")
        if section_id:
            for i in range(1, self.section_combo.count()):
                if self.section_combo.itemData(i) == section_id:
                    self.section_combo.setCurrentIndex(i)
                    break

        # Дата
        if self.current_filters.get("date_from"):
            self.date_from.setDate(QDate.fromString(self.current_filters["date_from"], "yyyy-MM-dd"))
            self.use_date_filter_checkbox.setChecked(True)  # Відмічаємо чекбокс, якщо є дата

        if self.current_filters.get("date_to"):
            self.date_to.setDate(QDate.fromString(self.current_filters["date_to"], "yyyy-MM-dd"))
            self.use_date_filter_checkbox.setChecked(True)

        # Кількість
        if "quantity_min" in self.current_filters:
            self.quantity_min_spin.setValue(self.current_filters["quantity_min"])
            self.use_quantity_filter_checkbox.setChecked(True)  # Відмічаємо чекбокс, якщо є мінімальна кількість

        if "quantity_max" in self.current_filters:
            self.quantity_max_spin.setValue(self.current_filters["quantity_max"])
            self.use_quantity_filter_checkbox.setChecked(True)



    def clear_fields(self):
        self.movement_type_combo.setCurrentIndex(0)
        self.product_combo.setCurrentIndex(-1)  # Очистити комбобокс продуктів
        self.section_combo.setCurrentIndex(0)
        self.date_from.setDate(QDate.currentDate())
        self.date_to.setDate(QDate.currentDate().addDays(1))
        self.quantity_min_spin.setValue(0)
        self.quantity_max_spin.setValue(0)
        self.use_date_filter_checkbox.setChecked(False)
        self.use_quantity_filter_checkbox.setChecked(False)
        self.current_filters = {}


