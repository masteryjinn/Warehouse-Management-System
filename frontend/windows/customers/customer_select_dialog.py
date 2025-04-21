import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, QMessageBox
)
from user_session.current_user import CurrentUser # Assuming you have a module to get the current user

class CustomerSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вибір клієнта")
        self.setMinimumSize(400, 400)
        self.selected_customer = None
        self.api_url = "http://localhost:8000/customers/select"  # URL to fetch customers from

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

        self.search_input.textChanged.connect(self.filter_customers)
        self.ok_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

        self.load_customers()

    def load_customers(self):
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
                raise Exception("Не вдалося завантажити клієнтів.")
            response.raise_for_status()
            self.customers = response.json()
            self.filtered_customers = self.customers.copy()
            self.update_list()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити клієнтів:\n{str(e)}")
            self.customers = []
            self.filtered_customers = []
            return

    def update_list(self):
        self.list_widget.clear()
        for customer in self.filtered_customers:
            self.list_widget.addItem(customer["name"])


    def filter_customers(self, text):
        self.filtered_customers = [
            c for c in self.customers if text.lower() in c["name"].lower()  # Порівнюємо з name
        ]
        self.update_list()


    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            name = current_item.text()
            selected = next((s for s in self.customers if s["name"] == name), None)
            self.selected_customer = selected  # Це буде словник: {"id": ..., "name": ...}
            self.accept()

    def get_selected_customer(self):
        return self.selected_customer  # Повний словник

