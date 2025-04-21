import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, QMessageBox
)
from user_session.current_user import CurrentUser # Assuming you have a module to get the current user

class SupplierSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вибір постачальника")
        self.setMinimumSize(400, 400)
        self.selected_supplier = None
        self.api_url = "http://localhost:8000/suppliers/select"  # URL to fetch suppliers from

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук...")

        self.list_widget = QListWidget()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Скасувати")

        layout = QVBoxLayout()
        layout.addWidget(self.search_input)
        layout.addWidget(self.list_widget)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.search_input.textChanged.connect(self.filter_suppliers)
        self.ok_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

        self.load_suppliers()

    def load_suppliers(self):
        try:
            current_user = CurrentUser()
            token = current_user.get_token()
            if not token:
                raise Exception("Токен не знайдений, перезайдіть, будь ласка.")
            response = requests.get(self.api_url, headers={
                "Authorization": f"Bearer {token}"
            })
            if response.status_code == 401:
                raise Exception("Токен недійсний, перезайдіть, будь ласка.")
            if response.status_code == 403:
                raise Exception("У вас немає доступу до цього ресурсу.")
            if response.status_code == 404:
                raise Exception("Ресурс не знайдений.")
            if response.status_code == 500:
                raise Exception("Внутрішня помилка сервера.")
            if response.status_code != 200:
                raise Exception("Не вдалося завантажити постачальників.")
            response.raise_for_status()
            self.suppliers = response.json()
            self.filtered_suppliers = self.suppliers.copy()
            self.update_list()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити постачальників:\n{str(e)}")
            self.suppliers = []
            self.filtered_suppliers = []
            return

    def update_list(self):
        self.list_widget.clear()
        for supplier in self.filtered_suppliers:
            self.list_widget.addItem(supplier["name"])


    def filter_suppliers(self, text):
        self.filtered_suppliers = [
            s for s in self.suppliers if text.lower() in s["name"].lower()  # Порівнюємо з name
        ]
        self.update_list()


    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            name = current_item.text()
            selected = next((s for s in self.suppliers if s["name"] == name), None)
            self.selected_supplier = selected  # Це буде словник: {"id": ..., "name": ...}
            self.accept()

    def get_selected_supplier(self):
        return self.selected_supplier  # Повний словник

