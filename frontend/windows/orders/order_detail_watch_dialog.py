from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser

class OrderDetailsDialog(QDialog):
    def __init__(self, order_id):
        super().__init__()
        self.setWindowTitle("Деталі замовлення")
        self.setMinimumSize(700, 400)
        self.order_id = order_id
        self.order_details = self.fetch_order_details(self.order_id)
        self.init_ui()

    def fetch_order_details(self, order_id):
        current_user = CurrentUser()
        token = current_user.get_token()
        response = requests.get(
            f'http://localhost:8000/orders/{order_id}/details',
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            return response.json()
        else:
            return []

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.order_label = QLabel(f"Замовлення №{self.order_id}")
        self.order_label.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.order_label)

        self.status_label = QLabel("Це замовлення не підлягає редагуванню.")
        self.status_label.setStyleSheet("color: #e74c3c; font-size: 16px; margin-bottom: 10px; font-weight: bold;")
        self.layout.addWidget(self.status_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Назва", "Кількість", "Розмірність", "Ціна", "Секція"])
        self.layout.addWidget(self.table)

        self.total_label = QLabel()  # Місце для суми
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        self.layout.addWidget(self.total_label)

        self.close_button = QPushButton("Закрити")
        self.close_button.clicked.connect(self.accept)
        self.layout.addWidget(self.close_button)

        self.setLayout(self.layout)

        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.populate_table()

        if not self.order_details:
            warning_label = QLabel(
                "Інформацію про замовлення не вдалося завантажити.\n"
                "Можливо, деякі продукти були видалені з бази даних."
            )
            warning_label.setStyleSheet("color: #c0392b; font-size: 14px; font-style: italic;")
            self.layout.addWidget(warning_label)

    def populate_table(self):
        if not self.order_details:
            return

        total_sum = 0.0

        for detail in self.order_details:
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            self.table.setItem(row_position, 0, QTableWidgetItem(detail["product_name"]))
            self.table.setItem(row_position, 1, QTableWidgetItem(str(detail["quantity"])))
            self.table.setItem(row_position, 2, QTableWidgetItem(detail["unit"]))
            self.table.setItem(row_position, 3, QTableWidgetItem(f"{detail['price']:.2f}"))
            self.table.setItem(row_position, 4, QTableWidgetItem(detail["section_name"]))

            # Підрахунок суми
            total_sum += detail["quantity"] * detail["price"]

        self.table.resizeRowsToContents()
        self.table.verticalHeader().setDefaultSectionSize(60)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Вивід суми
        self.total_label.setText(f"Загальна сума замовлення: {total_sum:.2f} грн")
