from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QLabel,
    QPushButton, QHBoxLayout, QMessageBox
)
from windows.employees.employee_select_dialog import EmployeeSelectDialog  # Імпортуйте ваш клас діалогу вибору працівника


class WarehouseDialog(QDialog):
    def __init__(self, warehouse=None):
        super().__init__()
        self.warehouse = warehouse
        self.setWindowTitle("Редагування складу" if warehouse else "Додавання складу")
        self.setFixedSize(300, 400)
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
            QComboBox {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 10px;
                color: white;
                font-size: 12pt;
            }
        """)

    def showEvent(self, event):
        super().showEvent(event)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Назва складу
        layout.addWidget(QLabel("Назва секції:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Локація:"))
        self.location_input = QLineEdit()
        layout.addWidget(self.location_input)

        # Кнопка для вибору працівника
        self.employee_button = QPushButton("Вибрати працівника")
        self.employee_button.clicked.connect(self.open_employee_dialog)
        layout.addWidget(self.employee_button)

        self.employee_label = QLabel("Відповідальний:")
        layout.addWidget(self.employee_label)

        self.employee_input = QLineEdit()
        self.employee_input.setReadOnly(True)  # Поле тільки для перегляду
        layout.addWidget(self.employee_input)

        # Кнопки для збереження і скасування
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Оновити" if self.warehouse else "Додати")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.save_button.clicked.connect(self.accept_with_validation)
        self.cancel_button.clicked.connect(self.reject)

        if self.warehouse:
            self.populate_fields()

    def open_employee_dialog(self):
        # Створюємо діалог для вибору працівника
        dialog = EmployeeSelectDialog()  # Створення діалогу для вибору працівника
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Якщо вибрано працівника, відображаємо його в полі
            selected_employee = dialog.get_selected_employee()
            if selected_employee:
                self.employee_input.setText(selected_employee["name"])

    def populate_fields(self):
        self.name_input.setText(self.warehouse.get("name", ""))
        self.location_input.setText(self.warehouse.get("location", ""))
        self.employee_input.setText(self.warehouse.get("employee_name", ""))

    def accept_with_validation(self):
        name = self.name_input.text().strip()
        location = self.location_input.text().strip()
        employee = self.employee_input.text().strip()

        # Перевірка на порожні поля
        if not name:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть назву складу.")
            return

        if not location:
            QMessageBox.warning(self, "Помилка", "Будь ласка, введіть локацію складу.")
            return

        if not employee:
            QMessageBox.warning(self, "Помилка", "Будь ласка, виберіть відповідального працівника.")
            return

        self.accept()  # Усе добре — приймаємо форму

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "location": self.location_input.text(),
            "employee_name": self.employee_input.text()
        }
