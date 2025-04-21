from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QGroupBox, QHBoxLayout, QSpacerItem, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
import requests
import csv
from styles.load_styles import load_styles
from user_session.current_user import CurrentUser

class HomeTab(QWidget):
    def __init__(self):
        super().__init__()

        self.api_url = 'http://localhost:8000/import'
        self.setStyleSheet(load_styles())

        # Основний лейаут
        home_layout = QVBoxLayout()

        # Блок для вітального повідомлення та опису програми
        message_box = QGroupBox()
        message_layout = QVBoxLayout()

        # Додамо картинку (наприклад, логотип) через QIcon
        logo_icon = QIcon("frontend/icons/main_pic.svg")  # Вкажіть шлях до вашого логотипа
        logo_label = QLabel()
        logo_label.setPixmap(logo_icon.pixmap(750, 800))  # Встановимо іконку з розмірами
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Вітальне повідомлення
        welcome_label = QLabel('Вітаємо, ви успішно увійшли в програму!')
        welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #333;")

        # Опис програми/компанії
        description_label = QLabel(
            'Ця програма забезпечує ефективне управління даними, включаючи працівників, клієнтів, постачальників, а також продукти, замовлення та склади. '
            'Ви отримуєте зручні інструменти для імпорту, аналізу та обробки інформації, що допомагають оптимізувати бізнес-процеси.')
        description_label.setWordWrap(True)  # Для зручності відображення тексту
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description_label.setStyleSheet("font-size: 14px; color: #555;")

        # Додамо все у message_box
        message_layout.addWidget(logo_label)
        message_layout.addWidget(welcome_label)
        message_layout.addWidget(description_label)

        # Кнопки імпорту, додані в message_layout
        self.import_employees_btn = QPushButton("Імпортувати працівників із CSV")
        self.import_customers_btn = QPushButton("Імпортувати клієнтів із CSV")
        self.import_suppliers_btn = QPushButton("Імпортувати постачальників із CSV")

        self.import_employees_btn.clicked.connect(lambda: self.import_data('employees'))
        self.import_customers_btn.clicked.connect(lambda: self.import_data('customers'))
        self.import_suppliers_btn.clicked.connect(lambda: self.import_data('suppliers'))
                # Додаємо message_box до головного лейауту
        message_box.setLayout(message_layout)
        message_box.setStyleSheet("background-color: #e3f3f9; border-radius: 10px; padding: 20px;")

        home_layout.addWidget(message_box)
        current_user = CurrentUser()
        if current_user.is_admin():
            btn_layout = QHBoxLayout()

            btn_layout.addWidget(self.import_employees_btn)
            btn_layout.addWidget(self.import_customers_btn)
            btn_layout.addWidget(self.import_suppliers_btn)

            home_layout.addLayout(btn_layout)

        # Додамо простір для відступу
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        home_layout.addItem(spacer)

        # Завершення оформлення
        self.setLayout(home_layout)

    def import_data(self, entity_type):
        current_user = CurrentUser()
        if not current_user.is_admin():
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Виберіть CSV файл", "", "CSV Files (*.csv)")
        if file_path:
            try:
                token = current_user.get_token()
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    data = [row for row in reader]

                response = requests.post(f"{self.api_url}/{entity_type}", json={"data": data}, headers={"Authorization": f"Bearer {token}"})

                if response.status_code == 200:
                    QMessageBox.information(self, "Успіх", f"Дані для {entity_type} імпортовано успішно.")
                else:
                    QMessageBox.critical(self, "Помилка", f"Помилка при імпорті: {response.text}")

            except Exception as e:
                QMessageBox.critical(self, "Помилка", str(e))
