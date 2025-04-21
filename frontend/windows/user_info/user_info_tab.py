from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser
from config.config import API_URL

class UserInfoTab(QWidget):
    def __init__(self, auth_window):
        super().__init__()
        self.auth_window = auth_window
        self.setWindowTitle("Особиста інформація")
        self.setStyleSheet("background-color: #283747; color: #ecf0f1;")

        layout = QVBoxLayout()

        header_layout = QHBoxLayout()
        title_label = QLabel("Ваші дані")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #ffffff; padding: 10px; font-weight: bold;")

        header_layout.addWidget(title_label)
        layout.addLayout(header_layout)

        self.table = QTableWidget()
        self.table.setRowCount(6)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Поле", "Значення"])
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #34495e;
                color: #ffffff;
                border: 1px solid #2c3e50;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #2c3e50;
            }
        """)

        fields = ["ID", "Ім'я", "Посада", "Email", "Телефон", "Адреса"]
        for row, field in enumerate(fields):
            item = QTableWidgetItem(field)
            item.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            item.setBackground(Qt.GlobalColor.transparent)
            self.table.setItem(row, 0, item)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()

        self.refresh_button = QPushButton("Оновити інформацію")
        self.refresh_button.setStyleSheet("""
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #16a085;
            }
            QPushButton:pressed {
                background-color: #148f77;
            }
        """)
        self.refresh_button.clicked.connect(self.fetch_employee_info)

        layout.addWidget(self.table)
        layout.addWidget(self.refresh_button)

        self.setLayout(layout)
        self.adjustSize()
        self.fetch_employee_info()

    def fetch_employee_info(self):
        current_user = CurrentUser()
        token = current_user.get_token()
        is_temp_password = current_user.get_is_temp_password()
        if not token and is_temp_password == 0:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            return

        try:
            response = requests.get(f"{API_URL}/user/info", headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                user_data = response.json()
                values = [
                    user_data['employee_id'],
                    user_data['name'],
                    user_data.get('position', 'Невизначено'),
                    user_data['email'],
                    user_data['phone'],
                    user_data['address']
                ]
                for row, value in enumerate(values):
                    item = QTableWidgetItem(str(value))
                    item.setFont(QFont("Arial", 12))
                    self.table.setItem(row, 1, item)
                self.table.resizeColumnsToContents()
                self.table.resizeRowsToContents()
                self.table.setMinimumWidth(self.table.horizontalHeader().length() + 50)
                self.table.setMinimumHeight(self.table.verticalHeader().length() + 50)
                self.adjustSize()
            elif response.status_code == 401:
                self.show_error("Токен недійсний або прострочений. Увійдіть у систему знову.")
                self.close()
                self.auth_window.show()
            else:
                self.show_error(f"Не вдалося отримати інформацію. Код помилки: {response.status_code}")
        except requests.exceptions.RequestException as req_err:
            self.show_error(f"Помилка запиту: {req_err}")

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)
