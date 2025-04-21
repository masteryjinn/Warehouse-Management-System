from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QMessageBox, QWidget, QComboBox, QLineEdit, QListView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QStringListModel
from PyQt6.QtGui import QIntValidator
import requests
from user_session.current_user import CurrentUser


class ProductSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пошук продуктів")
        self.setMinimumSize(400, 300)
        self.available_products = None
        self.filtered_products = None  # Початково всі продукти

    def showEvent(self, event):
        super().showEvent(event)
        self.available_products=self.get_available_products()
        self.filtered_products=self.available_products
        self.init_ui()

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
        layout = QVBoxLayout()

        self.search_label = QLabel("Пошук продуктів")
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Введіть назву продукту для пошуку...")
        self.search_input.textChanged.connect(self.filter_products)

        self.product_list_view = QListView(self)
        self.product_list_model = QStringListModel()
        self.product_list_view.setModel(self.product_list_model)
        self.product_list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.product_list_view.clicked.connect(self.select_product)

        layout.addWidget(self.search_label)
        layout.addWidget(self.search_input)
        layout.addWidget(self.product_list_view)

        self.setLayout(layout)
        self.update_product_list()

    def get_available_products(self):
        try:
            current_user=CurrentUser()
            token=current_user.get_token()
            res = requests.get("http://localhost:8000/products/all", headers={"Authorization": f"Bearer {token}"})
            res.raise_for_status()
            return res.json()
        except requests.RequestException as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося отримати доступні продукти: {e}")
            return []

    def filter_products(self):
        query = self.search_input.text().lower()
        self.filtered_products = [product for product in self.available_products if query in product["name"].lower()]
        self.update_product_list()

    def update_product_list(self):
        product_names = [product["name"] for product in self.filtered_products]
        self.product_list_model.setStringList(product_names)

    def select_product(self, index):
        product_name = self.product_list_model.data(index, Qt.ItemDataRole.DisplayRole)
        selected_product = next(product for product in self.filtered_products if product["name"] == product_name)
        self.accept()  # Закрити вікно пошуку
        self.selected_product = selected_product


class AddIncomingDialog(QDialog):
    def __init__(self, order_id=-1):
        super().__init__()
        self.setWindowTitle("Записати надходження товару")
        self.setMinimumSize(700, 400)
        self.selected_products = []
        self.order_id = order_id
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            background-color: #283747; color: #ecf0f1;
            QTableWidget { background-color: #34495e; color: #ffffff; font-size: 16px; }
            QPushButton { background-color: #1abc9c; color: white; font-size: 16px; }
        """)
        layout = QVBoxLayout()

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Назва", "Кількість", "Розмірність", "Секція"])
        layout.addWidget(self.table)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Додати продукт")
        self.confirm_button = QPushButton("Підтвердити")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.add_button.clicked.connect(self.add_product_row)
        self.confirm_button.clicked.connect(self.confirm_income)

    def add_product_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Відкриваємо діалог для пошуку продуктів
        search_dialog = ProductSearchDialog(self)
        if search_dialog.exec():
            selected_product = search_dialog.selected_product
            if not selected_product:
                return

            # Назва продукту
            name_item = QTableWidgetItem(selected_product["name"])
            name_item.setData(Qt.ItemDataRole.UserRole, selected_product)  # зберігаємо всі дані
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 0, name_item)

            # Кількість — тепер QLineEdit з валідацією
            qty_input = QLineEdit()
            qty_input.setPlaceholderText("Введіть кількість")
            qty_input.setValidator(QIntValidator(1, 1000000))  # дозволяє лише позитивні цілі числа
            self.table.setCellWidget(row_position, 1, qty_input)


            # Розмірність
            dimension_item = QTableWidgetItem(selected_product["unit"])
            dimension_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 2, dimension_item)

            # Секція
            section_item = QTableWidgetItem(selected_product["section_name"])
            section_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 3, section_item)
            
        self.table.resizeRowsToContents()
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter)

    def confirm_income(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Помилка", "Додайте хоча б один продукт.")
            return
        self.accept()

    def get_income_items(self):
        items = []
        for row in range(self.table.rowCount()):
            name_item = self.table.item(row, 0)
            if name_item is None:
                continue
            product = name_item.data(Qt.ItemDataRole.UserRole)

            qty_input = self.table.cellWidget(row, 1)
            if qty_input is None or not qty_input.text().isdigit():
                QMessageBox.warning(self, "Помилка", f"Невірна кількість у рядку {row+1}.")
                return []

            qty = int(qty_input.text())

            items.append({
                "product_id": product["product_id"],
                "quantity": qty,
                "unit": product["unit"],
                "section": product["section_name"]
            })
        return items