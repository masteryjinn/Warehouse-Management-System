from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QSpinBox, QMessageBox, QWidget, QComboBox, QLineEdit, QListView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QStringListModel
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
            res = requests.get("http://localhost:8000/products/available", headers={"Authorization": f"Bearer {token}"})
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


class OrderCreateDialog(QDialog):
    def __init__(self, order_id=-1):
        super().__init__()
        self.setWindowTitle("Створити замовлення")
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

        self.order_label = QLabel(f"Створення нового замовлення №{self.order_id}")
        self.order_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(self.order_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Назва", "Кількість", "Розмірність", "Ціна", "Секція"])
        layout.addWidget(self.table)
        self.total_label = QLabel("Загальна сума: 0.00 грн")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.total_label)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Додати продукт")
        self.confirm_button = QPushButton("Підтвердити")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.confirm_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.add_button.clicked.connect(self.add_product_row)
        self.confirm_button.clicked.connect(self.confirm_order)

    def add_product_row(self):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        # Відкриваємо діалог для пошуку продуктів
        search_dialog = ProductSearchDialog(self)
        if search_dialog.exec():
            selected_product = search_dialog.selected_product
            if not selected_product:
                return

            # Вибір продукту
            product_combo = QComboBox()
            product_combo.addItem(selected_product["name"], selected_product)
            self.table.setCellWidget(row_position, 0, product_combo)

            # Кількість
            qty_spin = QSpinBox()
            qty_spin.setMinimum(1)
            qty_spin.setMaximum(selected_product["available_quantity"])
            qty_spin.setValue(1)
            self.table.setCellWidget(row_position, 1, qty_spin)

            # Розмірність
            dimension_item = QTableWidgetItem(selected_product["unit"])
            dimension_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 2, dimension_item)

            # Ціна
            price_item = QTableWidgetItem(f"{selected_product['price']:.2f}")
            price_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 3, price_item)

            # Секція
            section_item = QTableWidgetItem(selected_product["section_name"])
            section_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row_position, 4, section_item)

            product_combo.currentIndexChanged.connect(lambda: self.update_row(row_position))
            qty_spin.valueChanged.connect(lambda: self.update_price(row_position))
            qty_spin.valueChanged.connect(self.update_total_sum)
            self.update_total_sum()


    def update_row(self, row):
        product_combo = self.table.cellWidget(row, 0)
        selected_product = product_combo.currentData()

        qty_spin = self.table.cellWidget(row, 1)
        qty_spin.setMaximum(selected_product["available_quantity"])

        self.table.setItem(row, 2, QTableWidgetItem(selected_product["unit"]))
        self.table.setItem(row, 4, QTableWidgetItem(selected_product["section_name"]))

        self.update_price(row)

    def update_price(self, row):
        product_combo = self.table.cellWidget(row, 0)
        selected_product = product_combo.currentData()
        qty = self.table.cellWidget(row, 1).value()
        price = selected_product["price"] * qty
        self.table.setItem(row, 3, QTableWidgetItem(f"{price:.2f}"))
        self.update_total_sum()

    def update_total_sum(self):
        total = 0.0
        for row in range(self.table.rowCount()):
            price_item = self.table.item(row, 3)
            if price_item:
                try:
                    total += float(price_item.text())
                except ValueError:
                    pass
        self.total_label.setText(f"Загальна сума: {total:.2f} грн")

    def confirm_order(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Помилка", "Додайте хоча б один продукт.")
            return
        self.accept()

    def get_order_items(self):
        items = []
        for row in range(self.table.rowCount()):
            product_combo = self.table.cellWidget(row, 0)
            if product_combo is None:
                continue  # пропустити рядок, якщо немає комбобокса

            product = product_combo.currentData()
            qty_widget = self.table.cellWidget(row, 1)
            if qty_widget is None:
                continue

            qty = qty_widget.value()

            items.append({
                "product_id": product["product_id"],
                "quantity": qty,
                "unit": product["unit"],
                "price": product["price"],
                "section": product["section_name"]
            })
        return items
