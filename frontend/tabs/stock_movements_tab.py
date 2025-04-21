from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QLabel, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser
from windows.stock_movements.add_incoming_dialog import AddIncomingDialog
from windows.stock_movements.filter_dialog import StockMovementFilterDialog
from windows.stock_movements.relocation_dialog import RelocationDialog
from styles.load_styles import load_styles

class StockMovementsTab(QWidget):
    def __init__(self,auth_window):
        super().__init__()
        self.current_page = 1
        self.items_per_page = 16
        self.total_pages = 1
        self.api_url="http://localhost:8000/stock_movements"
        self.auth_window=auth_window
        self.movement_type_filter = None
        self.product_id_filter = None
        self.section_id_filter = None
        self.date_from_filter = None
        self.date_to_filter = None
        self.quantity_min_filter = None
        self.quantity_max_filter = None
        self.filters = {}  # фільтри: movement_type, product_id, date_from, date_to
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_stock_movements()

    def init_ui(self):
        self.setStyleSheet(load_styles())
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        pagination_layout = QHBoxLayout()

        self.btn_add_incoming = QPushButton("Додати надходження")
        self.btn_relocate = QPushButton("Змінити місце зберігання")
        self.btn_filter = QPushButton("Фільтрувати")
        self.btn_add_incoming.clicked.connect(self.open_add_incoming_dialog)
        self.btn_relocate.clicked.connect(self.open_relocation_dialog)
        self.btn_filter.clicked.connect(self.open_filter_dialog)

        btn_layout.addWidget(self.btn_add_incoming)
        btn_layout.addWidget(self.btn_relocate)
        btn_layout.addWidget(self.btn_filter)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Товар", "Тип руху", "Кількість", "Дата", 'Секція',"Причина переміщення"
        ])
        self.table.horizontalHeader().setStretchLastSection(True)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Попередня")
        self.next_btn = QPushButton("Наступна")
        self.page_label = QLabel(f"Сторінка {self.current_page} з {self.total_pages}")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prev_btn.clicked.connect(self.on_prev_page)
        self.next_btn.clicked.connect(self.on_next_page)

        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)

        layout.addWidget(self.table)
        layout.addLayout(btn_layout)
        layout.addLayout(pagination_layout)
        self.setLayout(layout)
    
    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_stock_movements()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_stock_movements()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def open_filter_dialog(self):
        dialog = StockMovementFilterDialog(self, self.filters)
        if dialog.exec():
            self.apply_filters(dialog)
            self.current_page = 1  # Якщо є пагінація
            self.load_stock_movements()
    
    def apply_filters(self, dialog):
        self.filters = dialog.get_filters()

        self.movement_type_filter = self.filters.get("movement_type")
        self.product_id_filter = self.filters.get("product_id")
        self.section_id_filter = self.filters.get("section_id")
        self.date_from_filter = self.filters.get("date_from")
        self.date_to_filter = self.filters.get("date_to")
        self.quantity_min_filter = self.filters.get("quantity_min")
        self.quantity_max_filter = self.filters.get("quantity_max")

        # Debug: можна вивести всі фільтри для перевірки
        print("Фільтри:")
        print("Тип руху:", self.movement_type_filter)
        print("ID продукту:", self.product_id_filter)
        print("ID секції:", self.section_id_filter)
        print("Дата від:", self.date_from_filter)
        print("Дата до:", self.date_to_filter)
        print("Кількість від:", self.quantity_min_filter)
        print("Кількість до:", self.quantity_max_filter)

    def load_stock_movements(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        self.table.clearContents()
        self.table.setRowCount(0)
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Товар", "Тип руху", "Кількість", "Дата", "Секція","Причина переміщення"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        token = current_user.get_token() 
        is_temp_password = current_user.get_is_temp_password()
        if is_temp_password == 1:
            return
        if token is None and is_temp_password==0:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        try:
            filters = {
                "movement_type": self.movement_type_filter,
                "product_id": self.product_id_filter,
                "section_id": self.section_id_filter,
                "date_from": self.date_from_filter,
                "date_to": self.date_to_filter,
                "quantity_min": self.quantity_min_filter,
                "quantity_max": self.quantity_max_filter,
            }

            params = {
                "page": self.current_page,
                "limit": self.items_per_page
            }

            # Побудова списку параметрів
            params_list = []

            for key, value in params.items():
                params_list.append((key, value))

            for key, value in filters.items():
                if isinstance(value, list):
                    for item in value:
                        params_list.append((key, item))
                elif value not in (None, ""):
                    params_list.append((key, value))
            response = requests.get(self.api_url, params=params_list,headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 401:
                self.show_error("Токен недійсний або прострочений. Увійдіть у систему знову.")
                self.close()
                self.auth_window.show() 
                return
            elif response.status_code != 200:
                try:
                    error_detail = response.json().get("detail")
                    if error_detail:
                        self.show_error(f"Помилка: {error_detail}")
                    else:
                        self.show_error("Сталася помилка при зчитуванні інформації про рух товарів.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при зчитуванні даних. Код: {response.status_code}")
                return 
            response.raise_for_status()
            
            # Обробка пагінації та даних
            data = response.json()
            if "items" not in data:
                self.show_error("Помилка: Невідомий формат відповіді від сервера.")
                return

            movements = data["items"]
            total_pages = data.get("total_pages", 1)
            total_items = data.get("total_items", 0)
            current_page = data.get("current_page", 1)

            # Оновлюємо пагінацію
            self.update_pagination(total_pages, current_page)
            
            self.table.setRowCount(len(movements))
            for row_idx, movement in enumerate(movements):
                index_number = (self.current_page - 1) * self.items_per_page + row_idx + 1
                self.table.setVerticalHeaderItem(row_idx, QTableWidgetItem(str(index_number)))
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(movement["movement_id"])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(movement["product_name"]))
                self.table.setItem(row_idx, 2, QTableWidgetItem(movement["movement_type"]))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(movement["quantity"])))
                self.table.setItem(row_idx, 4, QTableWidgetItem(movement["movement_date"]))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(movement["section_name"])))
                self.table.setItem(row_idx,6, QTableWidgetItem(str(movement["movement_reason"])))

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити рух товарів:\n{str(e)}")

    def open_add_incoming_dialog(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        if token is None:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        dialog = AddIncomingDialog()
        if dialog.exec():
            data = dialog.get_income_items()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            try:
                res = requests.post(self.api_url, json=data, headers={"Authorization": f"Bearer {token}"})
                if res.status_code == 401:
                    self.show_error("Токен недійсний або прострочений. Увійдіть у систему знову.")
                    self.close()
                    self.auth_window.show() 
                    return
                
                elif res.status_code != 200:
                    try:
                        error_detail = res.json().get("detail")
                        if error_detail:
                            self.show_error(f"Помилка: {error_detail}")
                        else:
                            self.show_error("Сталася помилка при додаванні даних про надходження товару.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Інформація про надходження товару додано")
                self.load_stock_movements()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")

    def open_relocation_dialog(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        if token is None:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        dialog = RelocationDialog(self)
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            try:
                res = requests.post(f"{self.api_url}/relocation", json=data, headers={"Authorization": f"Bearer {token}"})
                if res.status_code == 401:
                    self.show_error("Токен недійсний або прострочений. Увійдіть у систему знову.")
                    self.close()
                    self.auth_window.show() 
                    return
                
                elif res.status_code != 200:
                    try:
                        error_detail = res.json().get("detail")
                        if error_detail:
                            self.show_error(f"Помилка: {error_detail}")
                        else:
                            self.show_error("Сталася помилка при додаванні даних про переміщення товару.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Інформація про переміщення товару додано")
                self.load_stock_movements()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)
