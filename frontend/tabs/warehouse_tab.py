from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel, QCheckBox
)
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser
from windows.warehouse.warehouse_dialog import WarehouseDialog
from styles.load_styles import load_styles

SECTION_TYPE_TRANSLATIONS = {
    "storage": "зберігання",
    "packaging": "пакування"
}


class SectionsTab(QWidget):
    def __init__(self, auth_window=None):
        super().__init__()
        self.auth_window = auth_window  # Змінна для зберігання вікна авторизації
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1
        self.api_url = "http://localhost:8000/sections"  # URL API
        self.search_query = ""

    def showEvent(self, event):
        super().showEvent(event)
        self.init_ui()
        self.load_sections()

    def init_ui(self):
        self.setStyleSheet(load_styles())

        layout = QVBoxLayout()

        # Пошук
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук по секції...")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")
        self.checkbox_empty_section = QCheckBox("Пустий склад")
        self.checkbox_empty_section.stateChanged.connect(self.perform_search)

        search_layout.addWidget(self.checkbox_empty_section)

        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Таблиця
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID', 'Назва', 'Тип секції', 'Місцезнаходження', 'Головний за склад', 'Телефон головного'])#може щось більш людське придумаєш то зміни
        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки

        current_user=CurrentUser()
        if(current_user.is_admin()):
            button_layout = QHBoxLayout()
            self.add_btn = QPushButton("Додати")
            self.edit_btn = QPushButton("Змінити")
            self.delete_btn = QPushButton("Видалити")

            self.add_btn.clicked.connect(self.add_section)
            self.edit_btn.clicked.connect(self.edit_section)
            self.delete_btn.clicked.connect(self.delete_section)
            button_layout.addWidget(self.add_btn)
            button_layout.addWidget(self.edit_btn)
            button_layout.addWidget(self.delete_btn)
            layout.addLayout(button_layout)
        else:
            self.items_per_page+=1

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
        self.load_sections()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.search_query = ""
        self.load_sections()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_sections()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_sections()

    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")
        self.prev_btn.setEnabled(current_page > 1)
        self.next_btn.setEnabled(current_page < total_pages)

    def load_sections(self):
        try:
            current_user = CurrentUser()
            if not (current_user.is_admin() or current_user.is_manager() or current_user.is_employee()):
                QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                self.close()
                return
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(6)
            self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
            self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
            self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            self.table.setHorizontalHeaderLabels(['ID', 'Назва', 'Тип секції', 'Місцезнаходження', 'Головний за склад', 'Телефон головного'])
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

            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_query,
                "is_empty": self.checkbox_empty_section.isChecked()
            }

            response = requests.get(self.api_url, headers=headers, params=params)

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
                        self.show_error("Сталася помилка при зчитуванні інформації про секції.")
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
                self.table.setItem(row, 0, QTableWidgetItem(str(section["section_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(section["name"]))
                section_type_ukr = SECTION_TYPE_TRANSLATIONS.get(section["section_type"], section["section_type"])
                self.table.setItem(row, 2, QTableWidgetItem(section_type_ukr))
                self.table.setItem(row, 3, QTableWidgetItem(section["location"]))
                self.table.setItem(row, 4, QTableWidgetItem(section["employee_name"]))
                self.table.setItem(row, 5, QTableWidgetItem(section["employee_phone"]))

            # Після заповнення таблиці даними:
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
            self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_section(self):
        current_user = CurrentUser()
        if not current_user.is_admin():
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        if token is None:
            self.show_error("Помилка: не знайдено токен авторизації. Будь ласка, увійдіть знову.")
            self.close()
            self.auth_window.show() 
            return
        dialog = WarehouseDialog()
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
                            self.show_error("Сталася помилка при додаванні нової секції.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при додаванні секції. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Секцію додано")
                self.load_sections()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")

    def edit_section(self):
        current_user = CurrentUser()
        if not current_user.is_admin():
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
            QMessageBox.warning(self, "Увага", "Оберіть секцію для редагування")
            return

        section_id = int(self.table.item(current_row, 0).text())
        section_data = {
            "name": self.table.item(current_row, 1).text(),
            "location": self.table.item(current_row, 3).text(),
            "employee_name": self.table.item(current_row, 4).text(),
        }

        dialog = WarehouseDialog(section_data)
        if dialog.exec():
            updated_data = dialog.get_data()
            if not updated_data:
                self.show_error("Помилка: дані не були введені.")
                return
            if not all(updated_data.values()):
               self.show_error("Помилка: всі поля повинні бути заповнені.")
               return
            try:
                res = requests.put(f"{self.api_url}/{section_id}", json=updated_data, headers={"Authorization": f"Bearer {token}"})
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
                            self.show_error("Сталася помилка при оновлені інформації про секцію.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при оновленні. Код: {res.status_code}")
                    return
                QMessageBox.information(self, "Оновлено", "Інформацію оновлено")
                self.load_sections()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося оновити: {e}")

    def delete_section(self):
        current_user = CurrentUser()
        if not current_user.is_admin():
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть секцію для видалення")
            return

        section_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText("Ви впевнені, що хочете видалити секцію?")
        confirm_box.setIcon(QMessageBox.Icon.Warning)
        confirm_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_box.setDefaultButton(QMessageBox.StandardButton.No)
        confirm_box.button(QMessageBox.StandardButton.Yes).setText("Так")
        confirm_box.button(QMessageBox.StandardButton.No).setText("Ні")

        # Показ і перевірка відповіді
        confirm = confirm_box.exec()
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            res = requests.delete(
                f"{self.api_url}/{section_id}",
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
                        self.show_error("Сталася помилка при видаленні секції.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                return

            QMessageBox.information(self, "Успіх", "Секцію видалено")
            self.load_sections()
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "Увага", "Сторінка порожня. Повертаємось на попередню сторінку.")
                if self.current_page>1:
                    self.current_page-=1
                    self.load_sections()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)