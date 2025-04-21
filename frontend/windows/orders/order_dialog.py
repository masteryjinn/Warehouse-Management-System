from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QMessageBox, QCheckBox, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QDateTime
from windows.customers.customer_select_dialog import CustomerSelectDialog  # Діалог вибору клієнта

class OrderDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Створення замовлення")
        self.setFixedSize(300, 300)
        self.selected_customer = None
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
            QComboBox {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 10px;
                color: white;
                font-size: 12pt;
            }
        """)

        layout = QVBoxLayout()

        # Кнопка вибору клієнта
        self.customer_button = QPushButton("Вибрати клієнта")
        self.customer_button.clicked.connect(self.open_customer_dialog)
        layout.addWidget(self.customer_button)

        self.customer_label = QLabel("Клієнт:")
        layout.addWidget(self.customer_label)

        self.customer_input = QLineEdit()
        self.customer_input.setReadOnly(True)
        layout.addWidget(self.customer_input)

        self.date_label = QLabel("Дата та час початку створення замовлення:")
        layout.addWidget(self.date_label)

        self.date_input = QDateTimeEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.date_input.setDateTime(QDateTime.currentDateTime())  # Встановлюємо поточну дату та час
        self.date_input.setReadOnly(True)  # Робимо поле тільки для перегляду (не редаговане)
        layout.addWidget(self.date_input)

        # Кнопки
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Створити")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.save_button.clicked.connect(self.accept_with_validation)
        self.cancel_button.clicked.connect(self.reject)

    def open_customer_dialog(self):
        dialog = CustomerSelectDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            customer = dialog.get_selected_customer()
            if customer:
                self.selected_customer = customer
                self.customer_input.setText(customer["name"])  # або інше представлення

    def accept_with_validation(self):
        if not self.selected_customer:
            QMessageBox.warning(self, "Помилка", "Будь ласка, оберіть клієнта.")
            return

        self.accept()

    def get_data(self):
        # Повертаємо поточну дату і час у форматі yyyy-MM-dd HH:mm:ss
        return {
            "customer_name": self.selected_customer["name"],
            "date": self.date_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        }
