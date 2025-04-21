from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton,
    QHBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QSpinBox
)
from PyQt6.QtCore import QDate, Qt
import requests
from user_session.current_user import CurrentUser
from windows.stock_movements.add_incoming_dialog import ProductSearchDialog
from PyQt6.QtWidgets import QMessageBox


class RelocationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Переміщення товарів")
        self.setFixedSize(700, 500)
        self.products = []  # список словників: {"product_id", "name", "quantity", "section"}

        self.sections = []

        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_options()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Випадний список секцій (цільова секція)
        layout.addWidget(QLabel("Нова секція:"))
        self.section_combo = QComboBox()
        layout.addWidget(self.section_combo)

        # Таблиця товарів
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Назва продукту", "Кількість", "Поточна секція"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        # Кнопки під таблицею
        button_table_layout = QHBoxLayout()
        self.product_search_button = QPushButton("Пошук продукту")
        self.delete_button = QPushButton("Видалити")
        self.confirm_button = QPushButton("Підтвердити переміщення")

        button_table_layout.addWidget(self.product_search_button)
        button_table_layout.addWidget(self.delete_button)
        button_table_layout.addStretch()
        button_table_layout.addWidget(self.confirm_button)
        layout.addLayout(button_table_layout)

        # Зв'язки кнопок
        self.product_search_button.clicked.connect(self.open_product_search)
        self.delete_button.clicked.connect(self.delete_selected_row)
        self.confirm_button.clicked.connect(self.validate_and_accept)

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
        except requests.RequestException as e:
            print(f"Помилка при завантаженні опцій: {e}")

    def open_product_search(self):
        dialog = ProductSearchDialog(self)
        if dialog.exec():
            selected_product = dialog.selected_product
            if selected_product:
                product_id = selected_product["product_id"]
                product_name = selected_product["name"]
                available_quantity = selected_product["available_quantity"]
                section_name = selected_product["section_name"]

                # Перевірка, чи вже додано
                for i in range(self.table.rowCount()):
                    if int(self.table.item(i, 0).data(Qt.ItemDataRole.UserRole)) == product_id:
                        QMessageBox.warning(self, "Увага", "Цей товар вже додано.")
                        return

                row_position = self.table.rowCount()
                self.table.insertRow(row_position)

                # Назва продукту
                item_name = QTableWidgetItem(product_name)
                item_name.setData(Qt.ItemDataRole.UserRole, product_id)
                self.table.setItem(row_position, 0, item_name)

                # Кількість (QSpinBox)
                quantity_spin = QSpinBox()
                quantity_spin.setMinimum(1)
                quantity_spin.setMaximum(available_quantity)
                quantity_spin.setValue(available_quantity)  # встановлюємо кількість на всю наявну кількість
                quantity_spin.setEnabled(False)  # вимикаємо можливість редагування
                self.table.setCellWidget(row_position, 1, quantity_spin)

                # Секція
                section_item = QTableWidgetItem(section_name)
                self.table.setItem(row_position, 2, section_item)

                self.table.resizeColumnsToContents()
                self.table.resizeRowsToContents()
                self.table.verticalHeader().setDefaultSectionSize(35)
                self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

    def delete_selected_row(self):
        selected = self.table.currentRow()
        if selected != -1:
            self.table.removeRow(selected)
        else:
            QMessageBox.warning(self, "Увага", "Оберіть рядок для видалення.")

    def get_data(self):
        target_section_index = self.section_combo.currentIndex()
        if target_section_index <= 0:
            QMessageBox.warning(self, "Помилка", "Оберіть секцію для переміщення.")
            return None

        target_section_id = self.section_combo.itemData(target_section_index)
        target_section_name = self.section_combo.currentText().strip()

        items = []

        for row in range(self.table.rowCount()):
            product_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            product_name = self.table.item(row, 0).text()
            quantity_widget = self.table.cellWidget(row, 1)
            quantity = quantity_widget.value() if quantity_widget else 1
            current_section_name = self.table.item(row, 2).text()

            items.append({
                "product_id": product_id,
                "quantity": quantity,
                "current_section": current_section_name
            })

        if not items:
            QMessageBox.warning(self, "Помилка", "Список продуктів для переміщення порожній.")
            return None

        return {
            "section_id": target_section_id,
            "items": items
        }


    def validate_and_accept(self):
        data = self.get_data()
        if not data:
            return

        target_section_id = data["section_id"]
        target_section_name = self.section_combo.currentText()

        nominal_moves = []
        invalid_moves = []

        for row in range(self.table.rowCount()):
            product_name = self.table.item(row, 0).text()
            current_section_name = self.table.item(row, 2).text()
            quantity_widget = self.table.cellWidget(row, 1)
            quantity = quantity_widget.value() if quantity_widget else 1

            if current_section_name == target_section_name:
                invalid_moves.append(product_name)

            if quantity == 0:
                nominal_moves.append(product_name)

        # Якщо є товари в тій самій секції
        if invalid_moves:
            QMessageBox.warning(
                self,
                "Помилка переміщення",
                f"Наступні товари вже знаходяться у секції '{target_section_name}':\n- " +
                "\n- ".join(invalid_moves)
            )
            return

        # Якщо є номінальні переміщення
        if nominal_moves:
            QMessageBox.information(
                self,
                "Номінальне переміщення",
                "Для наступних товарів кількість = 0, тому переміщення буде номінальним (без запису):\n- " +
                "\n- ".join(nominal_moves)
            )

        self.accept()


    def get_final_data(self):
        return self.get_data()
