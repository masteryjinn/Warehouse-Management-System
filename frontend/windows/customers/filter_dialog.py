from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout


class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Фільтри клієнтів")
        self.setFixedSize(320, 550)
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
        self.current_filters = parent.__dict__  # Отримуємо доступ до фільтрів головного вікна
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Ім’я
        layout.addWidget(QLabel("Ім’я містить:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        # Тип клієнта
        layout.addWidget(QLabel("Тип клієнта:"))
        self.type_input = QComboBox()
        self.type_input.addItem("Будь-який")
        self.type_input.addItem("Фізична особа")
        self.type_input.addItem("Юридична особа")
        layout.addWidget(self.type_input)

        # Наявність email
        layout.addWidget(QLabel("Email:"))
        self.email_input = QComboBox()
        self.email_input.addItems(["Будь-який", "Присутній", "Відсутній"])
        layout.addWidget(self.email_input)

        # Наявність телефону
        layout.addWidget(QLabel("Телефон:"))
        self.phone_input = QComboBox()
        self.phone_input.addItems(["Будь-який", "Присутній", "Відсутній"])
        layout.addWidget(self.phone_input)

        # Наявність адреси
        layout.addWidget(QLabel("Адреса:"))
        self.address_input = QComboBox()
        self.address_input.addItems(["Будь-який", "Присутній", "Відсутній"])
        layout.addWidget(self.address_input)

        # Кнопки
        button_layout = QVBoxLayout()
        self.apply_button = QPushButton("Застосувати")
        self.clear_button = QPushButton("Очистити")
        self.cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.apply_button.clicked.connect(self.accept)
        self.clear_button.clicked.connect(self.clear_fields)
        self.cancel_button.clicked.connect(self.reject)

        self.load_current_filters()

    def get_filters(self):
        filters = {}

        # Ім’я
        if self.name_input.text():
            filters["name_filter"] = self.name_input.text()

        # Тип клієнта (Фізична / Юридична)
        type_map = {
            "Фізична особа": "individual",
            "Юридична особа": "business"
        }
        selected_type = self.type_input.currentText()
        if selected_type in type_map:
            filters["type_filter"] = type_map[selected_type]

        map = {
            "Будь-який": None,
            "Присутній": True,
            "Відсутній": False
        }
        filters["email_required"] = map[self.email_input.currentText()]
        filters["phone_required"] = map[self.phone_input.currentText()]
        filters["address_required"] = map[self.address_input.currentText()]

        return filters

    def load_current_filters(self):
        if "name_filter" in self.current_filters:
            self.name_input.setText(self.current_filters["name_filter"])

        if "type_filter" in self.current_filters:
            type_map_reverse = {
                "individual": "Фізична особа",
                "business": "Юридична особа"
            }
            selected = type_map_reverse.get(self.current_filters["type_filter"], "Будь-який")
            index = self.type_input.findText(selected)
            self.type_input.setCurrentIndex(index if index != -1 else 0)

        def set_combo_value(combo_box, value):
            if value is None:
                combo_box.setCurrentText("Будь-який")
            elif value is True:
                combo_box.setCurrentText("Присутній")
            elif value is False:
                combo_box.setCurrentText("Відсутній")

        set_combo_value(self.email_input, self.current_filters.get("email_required"))
        set_combo_value(self.phone_input, self.current_filters.get("phone_required"))
        set_combo_value(self.address_input, self.current_filters.get("address_required"))

    def clear_fields(self):
        self.name_input.clear()
        self.type_input.setCurrentIndex(0)
        self.email_input.setCurrentIndex(0)
        self.phone_input.setCurrentIndex(0)
        self.address_input.setCurrentIndex(0)
