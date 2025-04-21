from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt
from user_session.current_user import CurrentUser
from PyQt6.QtWidgets import QFileDialog, QComboBox
from windows.products.product_filter_dialog import FilterDialog
from windows.products.product_dialog import ProductDialog
import requests
import pandas as pd
from styles.load_styles import load_styles

class ProductsTab(QWidget):
    def __init__(self, auth_window=None):
        super().__init__()
        self.auth_window = auth_window
        self.current_page = 1
        self.items_per_page = 13
        self.total_pages = 1
        self.api_url = "http://localhost:8000/products"  # URL API для продуктів
        self.name_filter = None
        self.category_filter = None
        self.price_min = None
        self.price_max = None
        self.sort_order = None
        self.filters= None
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(load_styles())
        
        layout = QVBoxLayout()

        # Створюємо основний лейаут для пошуку
        search_layout = QHBoxLayout()

        # Поле для введення тексту пошуку
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук по продукту...")

        # Кнопки пошуку і скидання
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")

        # Чекбокси для фільтрації за терміном придатності
        self.checkbox_expire_date = QCheckBox("Мають термін придатності")
        self.checkbox_expire_date.stateChanged.connect(self.perform_search)
        self.checkbox_has_expire = QCheckBox("Термін придатності закінчився")
        self.checkbox_has_expire.stateChanged.connect(self.perform_search)
        # Створюємо комбобокс для вибору секції
        self.section_combobox = QComboBox()
        self.section_combobox.addItem("Усі секції")  # Значення за замовчуванням
        self.section_combobox.currentTextChanged.connect(self.perform_search)

        # Організуємо чекбокси в горизонтальний лейаут
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox_expire_date)
        checkbox_layout.addWidget(self.checkbox_has_expire)
        checkbox_layout.addWidget(self.section_combobox)


        # Додаємо всі елементи до основного лейауту
        search_layout.addLayout(checkbox_layout)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        # З'єднуємо кнопки з відповідними методами
        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Можна також застосувати стиль для кнопок, щоб зробити їх більш помітними:
        #self.btn_search.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        #self.btn_clear.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Категорія', 'Ціна', 'Опис', 'Кількість', 'Роздільність', 'Термін придатності', 'Постачальник', 'Секція'])
        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки
        button_layout = QHBoxLayout()
        self.add_btn = QPushButton("Додати")
        self.edit_btn = QPushButton("Редагувати")
        self.delete_btn = QPushButton("Видалити")
        self.filter_btn = QPushButton("Фільтр")
        self.export_btn = QPushButton("Експорт")

        self.export_btn.clicked.connect(self.export_products)
        self.add_btn.clicked.connect(self.add_product)
        self.edit_btn.clicked.connect(self.edit_product)
        self.delete_btn.clicked.connect(self.delete_product)
        self.filter_btn.clicked.connect(self.open_filter_dialog)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addWidget(self.filter_btn)
        button_layout.addWidget(self.export_btn)
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
        self.load_products()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.load_products()

    def showEvent(self, event):
        super().showEvent(event)
        self.load_products()
        self.load_sections()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_products()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_products()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def open_filter_dialog(self):
        dialog = FilterDialog(self, self.api_url,self.filters)
        if dialog.exec():
            self.apply_filters(dialog)
            self.current_page = 1
            self.load_products()

    def apply_filters(self, dialog):
        self.filters = dialog.get_filters()
        self.name_filter = self.filters.get("name")
        self.category_filter = self.filters.get("categories")
        self.price_min = self.filters.get("min_price")
        self.price_max = self.filters.get("max_price")
        self.sort_order = self.filters.get("sort")  # Додано для сортування, якщо потрібно

        # Додатково можна перевірити чи є вибрані категорії та інші фільтри
        print(self.name_filter, self.category_filter, self.price_min, self.price_max, self.sort_order)

    def load_sections(self):
        try:
            current_user = CurrentUser()
            token = current_user.get_token()
            if not token:
                return

            response = requests.get("http://localhost:8000/sections/full", headers={"Authorization": f"Bearer {token}"})
            if response.status_code == 200:
                sections = response.json().get("sections", [])
                self.section_combobox.clear()
                self.section_combobox.addItem("Усі секції")
                for section in sections:
                    name = section.get("name")
                    if name:
                        self.section_combobox.addItem(name)
            else:
                print("Не вдалося завантажити секції:", response.status_code)
        except Exception as e:
            print("Помилка при завантаженні секцій:", str(e))

    def export_products(self):
        # Створення діалогового вікна для вибору файлу
        file_path, _ = QFileDialog.getSaveFileName(self, "Зберегти файл", "", "CSV Files (*.csv);;All Files (*)")
        
        # Перевірка, чи було обрано файл
        if file_path:
            # Перевірка наявності розширення CSV
            if not file_path.lower().endswith(".csv"):
                file_path += ".csv"

            try:
                # Отримання токена поточного користувача
                current_user = CurrentUser()
                if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
                    QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                    self.close()
                    return
                token = current_user.get_token()  # Отримуємо токен користувача
                if not token:
                    QMessageBox.warning(self, "Помилка", "Не вдалося отримати токен користувача.")
                    return

                filters = {
                    "name_filter": self.name_filter,
                    "category_filter": self.category_filter,
                    "price_min": self.price_min,
                    "price_max": self.price_max,
                    "sort_order": self.sort_order,
                }

                params = {
                    "search": self.search_input.text(),
                    "expire_date": self.checkbox_expire_date.isChecked(),
                    "has_expired": self.checkbox_has_expire.isChecked()
                }

                # Побудова списку параметрів
                params_list = []

                for key, value in params.items():
                    params_list.append((key, value))

                selected_section = self.section_combobox.currentText()
                if selected_section and selected_section != "Усі секції":
                    params_list.append(("section", selected_section))

                for key, value in filters.items():
                    if isinstance(value, list):
                        for item in value:
                            params_list.append((key, item))
                    elif value not in (None, ""):
                        params_list.append((key, value))

                # GET-запит з правильними параметрами
                response = requests.get(
                    f"{self.api_url}/full",
                    headers={"Authorization": f"Bearer {token}"},
                    params=params_list
                )

                # Перевірка статусу відповіді
                if response.status_code == 200:
                    # Отримуємо продукти у вигляді JSON
                    products_data = response.json().get("products", [])
                    
                    # Якщо дані є, створюємо DataFrame
                    if products_data:
                        df = pd.DataFrame(products_data)

                        # Записуємо дані в CSV
                        df.to_csv(file_path, index=False)

                        QMessageBox.information(self, "Успіх", f"Файл успішно збережено в {file_path}")
                    else:
                        QMessageBox.warning(self, "Помилка", "Не знайдено продуктів для експорту.")
                else:
                    QMessageBox.warning(self, "Помилка", f"Не вдалося отримати дані з сервера. Статус: {response.status_code}")
            except requests.exceptions.RequestException as req_err:
                QMessageBox.warning(self, "Помилка", f"Помилка запиту: {req_err}")
            except Exception as e:
                QMessageBox.warning(self, "Помилка", f"Сталася помилка при збереженні файлу: {str(e)}")

    def load_products(self):
        try:
            current_user = CurrentUser()
            if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
                QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                self.close()
                return
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(10)
            self.table.setHorizontalHeaderLabels(['ID', 'Ім’я', 'Категорія', 'Ціна', 'Опис', 'Кількість', 'Роздільність', 'Термін придатності', 'Постачальник', 'Секція'])
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

            token = current_user.get_token()
            if token is None:
                self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
                self.close()
                return

            filters = {
                "name_filter": self.name_filter,
                "category_filter": self.category_filter,
                "price_min": self.price_min,
                "price_max": self.price_max,
                "sort_order": self.sort_order,
            }

            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_input.text(),
                "expire_date": self.checkbox_expire_date.isChecked(),
                "has_expired": self.checkbox_has_expire.isChecked()
            }

            # Побудова списку параметрів
            params_list = []

            for key, value in params.items():
                params_list.append((key, value))

            selected_section = self.section_combobox.currentText()
            if selected_section and selected_section != "Усі секції":
                params_list.append(("section", selected_section))

            for key, value in filters.items():
                if isinstance(value, list):
                    for item in value:
                        params_list.append((key, item))
                elif value not in (None, ""):
                    params_list.append((key, value))

            # GET-запит з правильними параметрами
            response = requests.get(
                self.api_url,
                headers={"Authorization": f"Bearer {token}"},
                params=params_list
            )

            if response.status_code == 401:
                self.show_error("Токен недійсний або прострочений. Увійдіть у систему знову.")
                self.close()
                return
            elif response.status_code != 200:
                self.show_error("Сталася помилка при зчитуванні даних про продукти.")
                return
            response.raise_for_status()

            data = response.json()
            if "data" not in data:
                self.show_error("Помилка: Невідомий формат відповіді від сервера.")
                return

            products = data["data"]
            total_pages = data.get("total_pages", 1)
            total_items = data.get("total_items", 0)
            current_page = data.get("current_page", 1)

            self.update_pagination(total_pages, current_page)

            self.table.setRowCount(len(products))
            for row, product in enumerate(products):
                index_number = (self.current_page - 1) * self.items_per_page + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))
                self.table.setItem(row, 0, QTableWidgetItem(str(product["product_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(product["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(product["category_name"]))
                self.table.setItem(row, 3, QTableWidgetItem(str(product["price"])))
                self.table.setItem(row, 4, QTableWidgetItem(product.get("description", "")))
                self.table.setItem(row, 5, QTableWidgetItem(str(product["quantity"])))
                self.table.setItem(row, 6, QTableWidgetItem(str(product["unit"])))
                self.table.setItem(row, 7, QTableWidgetItem(product.get("expiration_date", "")))
                self.table.setItem(row, 8, QTableWidgetItem(product.get("supplier_name", "")))
                self.table.setItem(row, 9, QTableWidgetItem(product.get("section_name", "")))

            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setColumnWidth(4, 300)  # 4 — індекс стовпця "Опис", 300 — ширина стовпця
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_product(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        if token is None:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            return
        dialog = ProductDialog(None, self.api_url)
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            try:
                response = requests.post(
                    self.api_url,
                    headers={"Authorization": f"Bearer {token}"},
                    json=data
                )
                response.raise_for_status()
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
                            self.show_error("Сталася помилка при додаванні даних.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні. Код: {response.status_code}")
                    return

                QMessageBox.information(self, "Успіх", "Продукцію успішно додано в систему")
                self.load_products()
            except requests.exceptions.RequestException as e:
                self.show_error(f"Сталася помилка при додаванні продукту: {e}")

    def edit_product(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        selected_row = self.table.selectedIndexes()
        if not selected_row:
            QMessageBox.warning(self, "Увага", "Будь ласка, виберіть продукт для редагування.")
            return
        product_id = self.table.item(selected_row[0].row(), 0).text()
        product_data={
            "name": self.table.item(selected_row[0].row(), 1).text(),
            "category": self.table.item(selected_row[0].row(), 2).text(),
            "price": self.table.item(selected_row[0].row(), 3).text(),
            "description": self.table.item(selected_row[0].row(), 4).text(),
            "quantity": self.table.item(selected_row[0].row(), 5).text(),
            "unit": self.table.item(selected_row[0].row(), 6).text(),
            "expiration_date": self.table.item(selected_row[0].row(), 7).text(),
            "supplier_name": self.table.item(selected_row[0].row(), 8).text()
        }
        dialog = ProductDialog(product_data, self.api_url)
        if dialog.exec():
            data = dialog.get_data()
            if not data:
                self.show_error("Помилка: дані не були введені.")
                return
            try:
                token = current_user.get_token()
                response = requests.put(
                    f"{self.api_url}/{product_id}",
                    headers={"Authorization": f"Bearer {token}"},
                    json=data
                )
                response.raise_for_status()
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
                            self.show_error("Сталася помилка при редагуванні цієї продукції.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при редагуванні. Код: {response.status_code}")
                    return

                QMessageBox.information(self, "Успіх", "Продукцію успішно відредаговано")
                self.load_products()
            except requests.exceptions.RequestException as e:
                self.show_error(f"Сталася помилка при редагуванні продукту: {e}")

    def delete_product(self):
        current_user = CurrentUser()
        if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть продукт для видалення")
            return

        product_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText("Ви впевнені, що хочете видалити цей продукт?")
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
                f"{self.api_url}/{product_id}",
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
                        self.show_error("Сталася помилка при видаленні цієї продукції.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                return

            QMessageBox.information(self, "Успіх", "Продукцію видалено")
            self.load_products()
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "Увага", "Сторінка порожня. Повертаємось на попередню сторінку.")
                if self.current_page>1:
                    self.current_page-=1
                    self.load_products()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")


    def show_error(self, message):
        QMessageBox.critical(self, "Помилка", message)
