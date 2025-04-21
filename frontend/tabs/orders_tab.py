from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser
from windows.orders.filter_dialog import FilterDialog
from windows.orders.order_dialog import OrderDialog
from windows.orders.order_detail_watch_dialog import OrderDetailsDialog
from windows.orders.order_details_dialog import OrderCreateDialog
from styles.load_styles import load_styles


class OrdersTab(QWidget):
    def __init__(self, auth_window=None):
        super().__init__()
        self.auth_window = auth_window  # Змінна для зберігання вікна авторизації
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1
        self.filters=None
        self.customer_name_filter = None
        self.status_filter = None
        self.date_min = None
        self.date_max = None
        self.status_translation = {
            "new": "Нове",
            "processing": "Опрацьовується",
            "shipped": "Відправлено"
        }
        self.api_url = "http://localhost:8000/orders"  # URL API
        self.search_query = ""
        self.init_ui()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_orders()

    def init_ui(self):
        self.setStyleSheet(load_styles())

        layout = QVBoxLayout()

        # Пошук
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук по замовленнях...")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Номер замовлення', 'Замовник', 'Дата створення замовлення', 'Статус замовлення'])
        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Додати")
        self.edit_btn = QPushButton("Змінити статус")
        self.delete_btn = QPushButton("Видалити")
        self.filter_btn = QPushButton("Фільтр")
        self.details_btn = QPushButton("Деталі замовлення")

        self.add_btn.clicked.connect(self.add_order)
        self.edit_btn.clicked.connect(self.edit_order_status)
        self.delete_btn.clicked.connect(self.delete_order)
        self.filter_btn.clicked.connect(self.open_filter_dialog)
        self.details_btn.clicked.connect(self.get_details_window)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.filter_btn)
        button_layout.addWidget(self.details_btn)
        layout.addLayout(button_layout)

        # Пагінація
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
        self.search_query = self.search_input.text()
        self.load_orders()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.search_query = ""
        self.load_orders()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_orders()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_orders()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def open_filter_dialog(self):
        # Створення діалогу без передачі фільтрів
        dialog = FilterDialog(self, self.filters)  # Передаємо головне вікно
        if dialog.exec():
            self.apply_filters(dialog)
            self.current_page=1
            self.load_orders()

    def apply_filters(self, dialog):
        self.filters = dialog.get_filters()
        self.customer_name_filter = self.filters.get("customer_name_filter")
        self.status_filter = self.filters.get("status_filter")
        self.date_min = self.filters.get("date_min")
        self.date_max = self.filters.get("date_max")

    def load_orders(self):
        try:
            current_user = CurrentUser()
            if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
                QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                self.close()
                return
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(4)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table.setHorizontalHeaderLabels(['Номер замовлення', 'Замовник', 'Дата створення замовлення', 'Статус замовлення'])
            token = current_user.get_token()
            is_temp_password=current_user.get_is_temp_password()
            if is_temp_password == 1:
                return
            if token is None and is_temp_password==0:
                self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
                self.close()
                self.auth_window.show() 
                return
            headers = {"Authorization": f"Bearer {token}"}

            filters = {
                    "customer_name_filter": self.customer_name_filter,
                    "status_filter": self.status_filter,
                    "date_min": self.date_min,
                    "date_max": self.date_max,
                }

            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_query,
            }

            params_list = []

            for key, value in params.items():
                params_list.append((key, value))

            for key, value in filters.items():
                if isinstance(value, list):
                    for item in value:
                        params_list.append((key, item))
                elif value not in (None, ""):
                    params_list.append((key, value))

            response = requests.get(self.api_url, headers=headers, params=params_list)

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
                        self.show_error("Сталася помилка при зчитуванні інформації про замовлення.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при зчитуванні даних. Код: {response.status_code}")
                return 
            response.raise_for_status()
            
            # Обробка пагінації та даних
            data = response.json()
            if "data" not in data:
                self.show_error("Помилка: Невідомий формат відповіді від сервера.")
                return

            data = response.json()
            sections = data["data"]
            total_pages = data["total_pages"]
            current_page = data["current_page"]

            self.update_pagination(total_pages, current_page)

            self.table.setRowCount(len(sections))
            for row, section in enumerate(sections):
                index_number = (self.current_page - 1) * self.items_per_page + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))
                self.table.setItem(row, 0, QTableWidgetItem(str(section["order_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(section["customer_name"]))
                self.table.setItem(row, 2, QTableWidgetItem(section["order_date"]))
                translated_status = self.status_translation.get(section["status"], section["status"])
                self.table.setItem(row, 3, QTableWidgetItem(translated_status))

            # Після заповнення таблиці даними:
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_order(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        if token is None:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        dialog = OrderDialog()
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            if not all(data.values()):
               self.show_error("Помилка: всі поля повинні бути заповнені.")
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
                            self.show_error("Сталася помилка при додаванні нового замовлення.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні замовлення. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Замовлення додано")
                self.load_orders()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")

    def edit_order_status(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть замовлення для оновлення статусу.")
            return

        order_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText(f"Ви впевнені, що хочете оновити статус замовлення №{order_id}?")
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
            res = requests.put(
                f"{self.api_url}/{order_id}",
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
                        self.show_error("Сталася помилка при оновленні статусу замовлення.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при оновленні статусу. Код: {res.status_code}")
                return

            QMessageBox.information(self, "Успіх", "Статус замовленя оновлено")
            self.load_orders()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")

    def delete_order(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть замовлення для видалення")
            return

        order_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText("Ви впевнені, що хочете видалити замовлення?")
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
                f"{self.api_url}/{order_id}",
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
                        self.show_error("Сталася помилка при видаленні замовлення.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                return

            QMessageBox.information(self, "Успіх", "Замовлення видалено")
            self.load_orders()
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "Увага", "Сторінка порожня. Повертаємось на попередню сторінку.")
                if self.current_page>1:
                    self.current_page-=1
                    self.load_orders()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")

    def get_details_window(self):
        current_user=CurrentUser()
        token= current_user.get_token()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть замовлення, щоб отримати детальну інформацію про нього")
            return
        order_id = int(self.table.item(current_row, 0).text())
        status_ukr = self.table.item(current_row, 3).text()
        # Інверсія словника
        inverse_translation = {v: k for k, v in self.status_translation.items()}
        # Переклад
        status_eng = inverse_translation.get(status_ukr)
        if status_eng == "new":
            dialog = OrderCreateDialog(order_id)
            if dialog.exec():
                order_items = dialog.get_order_items()
                if not order_items:
                    self.show_error("Помилка: дані не були введені.")
                    return
                payload = {"items": order_items}
                try:
                    confirm_response = requests.post(
                        f"http://localhost:8000/orders/{order_id}/confirm",
                        json=payload,
                        headers={"Authorization": f"Bearer {token}"}
                    )
                    confirm_response.raise_for_status()
                    QMessageBox.information(self, "Успіх", "Замовлення успішно підтверджено та обробляється.")
                    self.load_orders()
                except requests.RequestException as e:
                    QMessageBox.critical(self, "Помилка", f"Не вдалося підтвердити замовлення: {e}")
        else:
            dialog = OrderDetailsDialog(order_id)
            dialog.exec()        

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)