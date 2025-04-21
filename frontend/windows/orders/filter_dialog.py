from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QCheckBox,
    QPushButton, QHBoxLayout, QListWidget, QDateEdit, QMessageBox
)
from PyQt6.QtCore import QDate
from windows.customers.customer_select_dialog import CustomerSelectDialog

class FilterDialog(QDialog):
    def __init__(self, parent=None, current_filters=None):
        super().__init__(parent)
        self.setWindowTitle("Фільтр замовлення")
        self.setFixedSize(400, 600)
        self.current_filters = current_filters or {}
        self.status_map = {
            "Нові": "new",
            "У процесі": "processing",
            "Відправлено": "shipped"
        }
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
        """)
        layout = QVBoxLayout(self)

        self.min_price_input = QLineEdit()
        self.max_price_input = QLineEdit()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["", "Нові", "У процесі", "Відправлено"])

        self.customer_button = QPushButton("Вибрати клієнта")
        self.customer_button.clicked.connect(self.open_customer_dialog)
        layout.addWidget(self.customer_button)

        self.customer_label = QLabel("Клієнт:")
        layout.addWidget(self.customer_label)

        self.customer_input = QLineEdit()
        self.customer_input.setReadOnly(True)
        layout.addWidget(self.customer_input)

        # ✅ Чекбокс для фільтрації за датою
        self.date_filter_checkbox = QCheckBox("Фільтрувати за датою")
        self.date_filter_checkbox.setChecked(True)
        self.date_filter_checkbox.stateChanged.connect(self.toggle_date_inputs)
        layout.addWidget(self.date_filter_checkbox)

        # 📅 Мінімальна дата
        layout.addWidget(QLabel("Мінімальна дата:"))
        self.date_min_input = QDateEdit(calendarPopup=True)
        self.date_min_input.setDisplayFormat("yyyy-MM-dd")
        self.date_min_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_min_input.setMinimumDate(QDate.currentDate().addYears(-1))
        self.date_min_input.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.date_min_input)

        # 📅 Максимальна дата
        layout.addWidget(QLabel("Максимальна дата:"))
        self.date_max_input = QDateEdit(calendarPopup=True)
        self.date_max_input.setDisplayFormat("yyyy-MM-dd")
        self.date_max_input.setDate(QDate.currentDate())
        self.date_max_input.setMinimumDate(QDate.currentDate().addYears(-1))
        self.date_max_input.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.date_max_input)

        layout.addWidget(QLabel("Статус замовлення:"))
        layout.addWidget(self.sort_combo)

        button_layout = QVBoxLayout()
        self.apply_button = QPushButton("Застосувати")
        self.clear_button = QPushButton("Очистити")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.apply_button.clicked.connect(self.validate_and_accept)
        self.clear_button.clicked.connect(self.clear_fields)
        self.cancel_button.clicked.connect(self.reject)

        self.load_current_filters()

    def toggle_date_inputs(self):
        enabled = self.date_filter_checkbox.isChecked()
        self.date_min_input.setEnabled(enabled)
        self.date_max_input.setEnabled(enabled)

    def open_customer_dialog(self):
        dialog = CustomerSelectDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_customer = dialog.get_selected_customer()
            if selected_customer:
                self.customer_input.setText(selected_customer["name"])

    def validate_and_accept(self):
        # Перевірка діапазону дат
        if self.date_filter_checkbox.isChecked():
            if self.date_min_input.date() > self.date_max_input.date():
                QMessageBox.warning(self, "Помилка", "Мінімальна дата не може бути пізніше за максимальну.")
                return
        
        if not self.customer_input:
            QMessageBox.warning(self, "Помилка", "Поле клієнта обов'язкове для заповнення.")
            return

        self.accept()

    def get_filters(self):
        filters = {}

        if self.date_filter_checkbox.isChecked():
            filters["date_min"] = self.date_min_input.date().toString("yyyy-MM-dd") + " 00:00:00"
            filters["date_max"] = self.date_max_input.date().toString("yyyy-MM-dd") + " 23:59:59"

        status_ukr = self.sort_combo.currentText()
        if status_ukr:
            filters["status_filter"] = self.status_map.get(status_ukr, "")


        customer_name = self.customer_input.text()
        if customer_name:
            filters["customer_name_filter"] = customer_name

        return filters

    def load_current_filters(self):
        self.customer_input.setText(self.current_filters.get("customer_name_filter", ""))

        date_min = self.current_filters.get("date_min")
        date_max = self.current_filters.get("date_max")
        if date_min and date_max:
            self.date_filter_checkbox.setChecked(True)
            self.date_min_input.setDate(QDate.fromString(date_min, "yyyy-MM-dd"))
            self.date_max_input.setDate(QDate.fromString(date_max, "yyyy-MM-dd"))
        else:
            self.date_filter_checkbox.setChecked(False)
            self.toggle_date_inputs()

        status_eng = self.current_filters.get("status_filter", "")
        # Пошук українського еквіваленту
        status_ukr = next((k for k, v in self.status_map.items() if v == status_eng), "")
        index = self.sort_combo.findText(status_ukr)
        self.sort_combo.setCurrentIndex(index if index >= 0 else 0)


    def clear_fields(self):
        self.sort_combo.setCurrentIndex(0)
        self.customer_input.clear()
        self.date_min_input.setDate(QDate.currentDate().addMonths(-1))
        self.date_max_input.setDate(QDate.currentDate())
        self.date_filter_checkbox.setChecked(False)
