from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel
)
from PyQt6.QtCore import Qt
from user_session.current_user import CurrentUser
from windows.customers.filter_dialog import FilterDialog
from windows.customers.add_customer_dialog import CustomerDialog
from styles.load_styles import load_styles
import requests

TYPE_MAP = {
    "business": "Юридична особа",
    "individual": "Фізична особа"
}

def translate_type_to_uk(type_en):
    return TYPE_MAP.get(type_en, type_en)

def translate_type_to_en(type_uk):
    inv_map = {v: k for k, v in TYPE_MAP.items()}
    return inv_map.get(type_uk, type_uk)


class CustomersTab(QWidget):
    def __init__(self, auth_window=None):
        super().__init__()
        self.auth_window = auth_window  # Змінна для зберігання вікна авторизації
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1
        self.api_url = "http://localhost:8000/customers"  # URL API
        self.name_filter = None
        self.type_filter = None
        self.email_required = None
        self.phone_required = None
        self.address_required = None
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_customers()

    def init_ui(self):
        self.setStyleSheet(load_styles())

        layout = QVBoxLayout()

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук по клієнту...")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Тип', 'Email', 'Телефон',  'Адреса'])
        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Додати")
        self.edit_btn = QPushButton("Редагувати")
        self.delete_btn = QPushButton("Видалити")
        self.filter_btn = QPushButton("Фільтр")

        self.add_btn.clicked.connect(self.add_customer)
        self.edit_btn.clicked.connect(self.edit_customer)
        self.delete_btn.clicked.connect(self.delete_customer)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.filter_btn)
        layout.addLayout(button_layout)

        # Кнопки для пагінації
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

        layout.addLayout(pagination_layout)

        self.setLayout(layout)

    def perform_search(self):
        self.current_page = 1
        self.load_customers()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.load_customers()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_customers()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_customers()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        
        # Оновлення інтерфейсу пагінації
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")

        # Логіка кнопок "Попередня" та "Наступна"
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def open_filter_dialog(self):
        # Створення діалогу без передачі фільтрів
        dialog = FilterDialog(self)  # Передаємо головне вікно
        if dialog.exec():
            self.apply_filters(dialog)
            self.current_page = 1
            self.load_customers()

    def apply_filters(self, dialog):
        filters = dialog.get_filters()
        self.name_filter = filters.get("name_filter")
        self.type_filter = filters.get("type_filter")
        self.email_required = filters.get("email_required")
        self.phone_required = filters.get("phone_required")
        self.address_required = filters.get("address_required")

    def load_customers(self):
        try:
            current_user = CurrentUser()
            if not (current_user.is_admin() or current_user.is_manager()):
                QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                self.close()
                return
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(6)
            self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Тип', 'Email', 'Телефон',  'Адреса'])
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
            # Отримуємо дані з API  
            filters = {
                "name_filter": self.name_filter,
                "type_filter": self.type_filter,
                "email_required": self.email_required,
                "phone_required": self.phone_required,
                "address_required": self.address_required,
            }

            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_input.text(),
            }

            if filters:
                params.update(filters)  # Додаємо фільтри до параметрі

            response = requests.get(
                self.api_url,
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )

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
                        self.show_error("Сталася помилка при зчитуванні інформації про клієнтів.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при зчитуванні даних. Код: {response.status_code}")
                return 
            response.raise_for_status()
            
            # Обробка пагінації та даних
            data = response.json()
            if "data" not in data:
                self.show_error("Помилка: Невідомий формат відповіді від сервера.")
                return

            customers = data["data"]
            total_pages = data.get("total_pages", 1)
            total_items = data.get("total_items", 0)
            current_page = data.get("current_page", 1)

            # Оновлюємо пагінацію
            self.update_pagination(total_pages, current_page)

            self.table.setRowCount(len(customers))
            for row, customer in enumerate(customers):
                index_number = (self.current_page - 1) * self.items_per_page + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))
                self.table.setItem(row, 0, QTableWidgetItem(str(customer["customer_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(customer["name"]))
                translated_type = translate_type_to_uk(customer["type"])
                self.table.setItem(row, 2, QTableWidgetItem(translated_type))
                self.table.setItem(row, 3, QTableWidgetItem(customer.get("email", "")))
                self.table.setItem(row, 4, QTableWidgetItem(customer.get("phone", "")))
                self.table.setItem(row, 5, QTableWidgetItem(customer.get("address", "")))

            # Після заповнення таблиці даними:
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_customer(self):
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
        dialog = CustomerDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            #if not all(data.values()):
             #   self.show_error("Помилка: всі поля повинні бути заповнені.")
              #  return
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
                            self.show_error("Сталася помилка при додаванні нового клієнта.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Клієнта додано")
                self.load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")


    def edit_customer(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        is_temp_password = current_user.get_is_temp_password()
        if token is None and is_temp_password==0:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть клієнта для редагування")
            return

        customer_id = int(self.table.item(current_row, 0).text())
        customer_data = {
            "name": self.table.item(current_row, 1).text(),
            "type": translate_type_to_en(self.table.item(current_row, 2).text()),
            "email": self.table.item(current_row, 3).text(),
            "phone": self.table.item(current_row, 4).text(),
            "address": self.table.item(current_row, 5).text(),
        }

        dialog = CustomerDialog(customer_data)
        if dialog.exec():
            updated_data = dialog.get_data()
            if not updated_data:
                self.show_error("Помилка: дані не були введені.")
                return
            try:
                res = requests.put(f"{self.api_url}/{customer_id}", json=updated_data, headers={"Authorization": f"Bearer {token}"})
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
                            self.show_error("Сталася помилка при оновленні інформації про клієнта.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при оновленні інформації про. Код: {res.status_code}")
                    return
                QMessageBox.information(self, "Оновлено", "Інформацію оновлено")
                self.load_customers()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося оновити: {e}")

    def delete_customer(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть клієнта для видалення")
            return

        customer_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText("Ви впевнені, що хочете видалити клієнта?")
        confirm_box.setIcon(QMessageBox.Icon.Warning)
        confirm_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_box.setDefaultButton(QMessageBox.StandardButton.No)
        confirm_box.button(QMessageBox.StandardButton.Yes).setText("Так")
        confirm_box.button(QMessageBox.StandardButton.No).setText("Ні")

        # Додатковий стиль (необов’язково)
        confirm_box.setStyleSheet("""
            QMessageBox {
                color: #ecf0f1;
                font-size: 14px;
            }
            QPushButton {
                min-width: 80px;
                font-size: 13px;
                padding: 5px 10px;
            }
        """)

        # Показ і перевірка відповіді
        confirm = confirm_box.exec()
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            res = requests.delete(
                f"{self.api_url}/{customer_id}",
                headers={"Authorization": f"Bearer {current_user.get_token()}"}
            )

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
                        self.show_error("Сталася помилка при видаленні клієнта.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                return

            QMessageBox.information(self, "Успіх", "Клієнта видалено")
            self.load_customers()
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "Увага", "Сторінка порожня. Повертаємось на попередню сторінку.")
                if self.current_page>1:
                    self.current_page-=1
                    self.load_customers()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")


    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)

    