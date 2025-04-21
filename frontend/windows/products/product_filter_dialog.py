from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QHBoxLayout, QListWidget, QListWidgetItem
from user_session.current_user import CurrentUser
from PyQt6.QtWidgets import QMessageBox
import requests

class FilterDialog(QDialog):
    def __init__(self,parent= None, api_url = None,current_filters=None):
        super().__init__(parent)
        self.setWindowTitle("Фільтр продуктів")
        self.setFixedSize(320, 640) 
        self.categories_list= None
        self.api_url=api_url
        self.sort_options = {
            "": "",
            "Ціна ↑": "price_asc",
            "Ціна ↓": "price_desc",
            "Кількість ↑": "quantity_asc",
            "Кількість ↓": "quantity_desc",
            "Назва ↑": "name_asc",
            "Назва ↓": "name_desc",
            "Термін придатності ↑": "expiration_date_asc",
            "Термін придатності ↓": "expiration_date_desc"
        }
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
        self.current_filters = current_filters or {}
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_categories() 

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
        layout = QVBoxLayout(self)

        self.name_input = QLineEdit()
        self.min_price_input = QLineEdit()
        self.max_price_input = QLineEdit()
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(list(self.sort_options.keys()))

        layout.addWidget(QLabel("Назва продукту:"))
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("Мінімальна ціна:"))
        layout.addWidget(self.min_price_input)
        layout.addWidget(QLabel("Максимальна ціна:"))
        layout.addWidget(self.max_price_input)
        layout.addWidget(QLabel("Сортування:"))
        layout.addWidget(self.sort_combo)

        # Група чекбоксів категорій
        layout.addWidget(QLabel("Категорії:"))
        self.categories_list = QListWidget()
        self.categories_list.setSelectionMode(QListWidget.SelectionMode.MultiSelection)
        layout.addWidget(self.categories_list)

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

    def update_category_list(self):
        self.categories_list.clear()
        if not hasattr(self, "categories"):
            return
        for category_name in self.categories:
            item = QListWidgetItem(category_name)
            self.categories_list.addItem(item)
        
        # Після створення списку категорій — завантажуємо фільтри
        self.load_current_filters()

    def load_categories(self):
        current_user = CurrentUser()
        token = current_user.get_token()
        if not token:
            QMessageBox.warning(self, "Помилка", "Не вдалося отримати токен користувача.")
            return

        try:
            res = requests.get(
                f"{self.api_url}/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            if res.status_code == 200:
                self.categories = res.json().get("categories", [])
                self.update_category_list()
            else:
                QMessageBox.warning(self, "Помилка", "Не вдалося отримати категорії.")
        except requests.exceptions.RequestException as req_err:
            print(f"Помилка запиту: {req_err}")
            QMessageBox.warning(self, "Помилка", f"Помилка запиту: {req_err}")

    def get_filters(self):
        filters = {}
        if self.name_input.text():
            filters["name"] = self.name_input.text()
        if self.min_price_input.text():
            filters["min_price"] = self.min_price_input.text()
        if self.max_price_input.text():
            filters["max_price"] = self.max_price_input.text()
        selected_sort_ukr = self.sort_combo.currentText()
        if selected_sort_ukr:
            filters["sort"] = self.sort_options.get(selected_sort_ukr, "")


        selected_categories = [item.text() for item in self.categories_list.selectedItems()]
        if selected_categories:
            filters["categories"] = selected_categories

        return filters

    def load_current_filters(self):
        # Перевіряємо, чи є збережені фільтри
        if not hasattr(self, "current_filters"):
            return

        # Встановлюємо значення текстових полів
        self.name_input.setText(self.current_filters.get("name", ""))
        self.min_price_input.setText(self.current_filters.get("min_price", ""))
        self.max_price_input.setText(self.current_filters.get("max_price", ""))

        # Встановлюємо обране сортування
        sort_value = self.current_filters.get("sort", "")
        ukr_label = next((k for k, v in self.sort_options.items() if v == sort_value), "")
        index = self.sort_combo.findText(ukr_label)
        if index >= 0:
            self.sort_combo.setCurrentIndex(index)
        else:
            self.sort_combo.setCurrentIndex(0)

        # Встановлюємо обрані категорії
        selected_categories = self.current_filters.get("categories", [])
        for i in range(self.categories_list.count()):
            item = self.categories_list.item(i)
            item.setSelected(item.text() in selected_categories)

    def clear_fields(self):
        self.name_input.clear()
        self.min_price_input.clear()
        self.max_price_input.clear()
        self.sort_combo.setCurrentIndex(0)
        self.categories_list.clearSelection()
        self.current_filters = {}



