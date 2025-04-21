import requests
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QListWidget, QPushButton, QHBoxLayout, QMessageBox
)
from user_session.current_user import CurrentUser # Assuming you have a module to get the current user

class EmployeeSelectDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вибір працівника")
        self.setMinimumSize(400, 400)
        self.selected_employee = None
        self.api_url = "http://localhost:8000/employees/select"  # URL to fetch employees from

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

        self.search_input.textChanged.connect(self.filter_employees)
        self.ok_button.clicked.connect(self.accept_selection)
        self.cancel_button.clicked.connect(self.reject)
        self.list_widget.itemDoubleClicked.connect(self.accept_selection)

        self.load_employees()

    def load_employees(self):
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
            self.employees = response.json()
            self.filtered_employees = self.employees.copy()
            self.update_list()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити постачальників:\n{str(e)}")
            self.employees = []
            self.filtered_employees = []
            return

    def update_list(self):
        self.list_widget.clear()
        for employee in self.filtered_employees:
            self.list_widget.addItem(employee["name"])


    def filter_employees(self, text):
        self.filtered_employees = [
            e for e in self.employees if text.lower() in e["name"].lower()  # Порівнюємо з name
        ]
        self.update_list()


    def accept_selection(self):
        current_item = self.list_widget.currentItem()
        if current_item:
            name = current_item.text()
            selected = next((e for e in self.employees if e["name"] == name), None)
            self.selected_employee = selected  # Це буде словник: {"id": ..., "name": ...}
            self.accept()

    def get_selected_employee(self):
        return self.selected_employee  # Повний словник

