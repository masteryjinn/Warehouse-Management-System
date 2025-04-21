from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QMessageBox, QDialog,  QCheckBox, QLabel
)
from PyQt6.QtCore import Qt
import requests
from user_session.current_user import CurrentUser
from config.config import API_URL 
from windows.employees.employee_form_dialog import EmployeeFormDialog
from windows.employees.register_employee_window import RegisterEmployeeWindow
from windows.employees.update_role_dialog import UpdateRoleDialog
from styles.load_styles import load_styles

class EmployeesTab(QWidget):
    def __init__(self, auth_window):
        super().__init__()
        self.auth_window = auth_window
        self.api_url = f"{API_URL}/employees"
        self.current_page = 1
        self.items_per_page = 15
        self.total_pages = 1

        self.init_ui()
    
    def showEvent(self, event):
        super().showEvent(event)
        self.load_data()

    def init_ui(self):
        self.setStyleSheet(load_styles())

        layout = QVBoxLayout()
        #####self.setLayout(self.layout)

        # Поле пошуку та фільтр
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Пошук за іменем, email або посадою...")
        self.btn_search = QPushButton("Пошук")
        self.btn_clear = QPushButton("Скинути")

        self.checkbox_unregistered = QCheckBox("Лише незареєстровані")
        self.checkbox_unregistered.stateChanged.connect(self.perform_search)

        search_layout.addWidget(self.checkbox_unregistered)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_search)
        search_layout.addWidget(self.btn_clear)

        # Таблиця співробітників
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "ID", "Ім'я", "Посада", "Email", "Телефон", "Адреса", "Зареєстрований"
        ])
        self.table.itemSelectionChanged.connect(self.on_employee_selected)
        layout.addLayout(search_layout)
        layout.addWidget(self.table)

        # Кнопки пошуку
        self.btn_search.clicked.connect(self.perform_search)
        self.btn_clear.clicked.connect(self.clear_search)

        # Кнопки CRUD
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Додати")
        self.btn_edit = QPushButton("Редагувати")
        self.btn_register = QPushButton("Зареєструвати")
        self.btn_delete = QPushButton("Видалити")

        self.btn_add.clicked.connect(self.add_employee)
        self.btn_edit.clicked.connect(self.edit_employee)
        self.btn_register.clicked.connect(self.register_employee)
        self.btn_delete.clicked.connect(self.delete_employee)

        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_register)
        btn_layout.addWidget(self.btn_delete)
        layout.addLayout(btn_layout)

        # Пагінація
        pagination_layout = QHBoxLayout()
        self.btn_prev_page = QPushButton("← Попередня")
        self.btn_next_page = QPushButton("Наступна →")
        self.page_label = QLabel(f"Сторінка {self.current_page} з {self.total_pages}")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        pagination_layout.addWidget(self.btn_prev_page)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.btn_next_page)
        layout.addLayout(pagination_layout)

        # Прив’язка кнопок до дій
        self.btn_prev_page.clicked.connect(self.on_prev_page)
        self.btn_next_page.clicked.connect(self.on_next_page)

        self.setLayout(layout)        

    def perform_search(self):
        self.current_page = 1
        self.load_data()

    def clear_search(self):
        self.search_input.clear()
        self.current_page = 1
        self.load_data()

    def on_prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.load_data()

    def on_next_page(self):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.load_data()

    def on_employee_selected(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            return
        is_registered = self.table.item(current_row, 6).text()
        if is_registered == "Так":
            self.btn_register.setText("Оновити роль")
        else:
            self.btn_register.setText("Зареєструвати")


    def update_pagination(self, total_pages, current_page):
        self.total_pages = total_pages
        self.current_page = current_page
        
        # Оновлення інтерфейсу пагінації
        self.page_label.setText(f"Сторінка {current_page} з {total_pages}")

        # Логіка кнопок "Попередня" та "Наступна"
        self.btn_prev_page.setEnabled(current_page > 1)
        self.btn_next_page.setEnabled(current_page < total_pages)


    def load_data(self):
        try:
            current_user = CurrentUser()
            if not current_user.is_admin():
                QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
                self.close()
                return
            self.table.clearContents()
            self.table.setRowCount(0)
            self.table.setColumnCount(7)
            self.table.setHorizontalHeaderLabels([
                "ID", "Ім'я", "Посада", "Email", "Телефон", "Адреса", "Зареєстрований"
            ])
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
            params = {
                "page": self.current_page,
                "limit": self.items_per_page,
                "search": self.search_input.text(),
                "registered_only": self.checkbox_unregistered.isChecked()  # використовуємо правильний параметр
            }

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
                        self.show_error("Сталася помилка при видаленні співробітника.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {response.status_code}")
                return 
            response.raise_for_status()
            
            # Обробка пагінації та даних
            data = response.json()
            if "data" not in data:
                self.show_error("Помилка: Невідомий формат відповіді від сервера.")
                return

            employees = data["data"]
            total_pages = data.get("total_pages", 1)
            total_items = data.get("total_items", 0)
            current_page = data.get("current_page", 1)

            # Оновлюємо пагінацію
            self.update_pagination(total_pages, current_page)

            self.table.setRowCount(len(employees))
            for row, emp in enumerate(employees):
                index_number = (self.current_page - 1) * self.items_per_page + row + 1
                self.table.setVerticalHeaderItem(row, QTableWidgetItem(str(index_number)))
                self.table.setItem(row, 0, QTableWidgetItem(str(emp["employee_id"])))
                self.table.setItem(row, 1, QTableWidgetItem(emp["name"]))
                self.table.setItem(row, 2, QTableWidgetItem(emp["position"]))
                self.table.setItem(row, 3, QTableWidgetItem(emp.get("email", "")))
                self.table.setItem(row, 4, QTableWidgetItem(emp.get("phone", "")))
                self.table.setItem(row, 5, QTableWidgetItem(emp.get("address", "")))
                self.table.setItem(row, 6, QTableWidgetItem("Так" if emp.get("is_registered", False) else "Ні"))

            # Після заповнення таблиці даними:
            self.table.resizeColumnsToContents()
            self.table.resizeRowsToContents()
            self.table.verticalHeader().setDefaultSectionSize(35)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити дані: {e}")

    def add_employee(self):
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
        dialog = EmployeeFormDialog(self)
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
                            self.show_error("Сталася помилка при видаленні співробітника.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                    return
                data = res.json()
                res.raise_for_status()
                QMessageBox.information(self, "Успіх", "Співробітника додано")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося додати: {e}")


    def edit_employee(self):
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
            QMessageBox.warning(self, "Увага", "Оберіть співробітника для редагування")
            return

        emp_id = int(self.table.item(current_row, 0).text())
        employee_data = {
            "name": self.table.item(current_row, 1).text(),
            "position": self.table.item(current_row, 2).text(),
            "email": self.table.item(current_row, 3).text(),
            "phone": self.table.item(current_row, 4).text(),
            "address": self.table.item(current_row, 5).text(),
        }

        dialog = EmployeeFormDialog(self, employee_data)
        if dialog.exec():
            updated_data = dialog.get_data()
            if not updated_data:
                self.show_error("Помилка: дані не були введені.")
                return
            if not all(updated_data.values()):
                self.show_error("Помилка: всі поля повинні бути заповнені.")
                return
            try:
                res = requests.put(f"{self.api_url}/{emp_id}", json=updated_data, headers={"Authorization": f"Bearer {token}"})
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
                            self.show_error("Сталася помилка при видаленні співробітника.")
                    except Exception as e:
                        self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                    return
                QMessageBox.information(self, "Оновлено", "Інформацію оновлено")
                self.load_data()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося оновити: {e}")

    def register_employee(self):
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

        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть співробітника")
            return

        registered = self.table.item(current_row, 6).text()
        #if registered == "Так":
            #QMessageBox.information(self, "Інформація", "Цей співробітник вже зареєстрований")
            #return

        emp_id = int(self.table.item(current_row, 0).text())
        if registered == "Так":
            # Якщо співробітник вже зареєстрований, відкриваємо діалог для зміни ролі
            dialog = UpdateRoleDialog(emp_id, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_data()
        else:
            # Створення вікна для реєстрації
            register_window = RegisterEmployeeWindow(emp_id, self.api_url, self)
            
            # Відкриваємо вікно реєстрації
            if register_window.exec() == QDialog.DialogCode.Accepted:
                self.load_data()  # Оновлюємо дані після успішної реєстрації

    def delete_employee(self):
        current_user = CurrentUser()
        if not current_user.is_admin():
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Увага", "Оберіть співробітника")
            return

        emp_id = int(self.table.item(current_row, 0).text())
        confirm_box = QMessageBox(self)
        confirm_box.setWindowTitle("Підтвердження дії")
        confirm_box.setText("Ви впевнені, що хочете видалити співробітника?")
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
                f"{self.api_url}/{emp_id}",
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
                        self.show_error("Сталася помилка при видаленні співробітника.")
                except Exception as e:
                    self.show_error(f"Сталася помилка при видаленні. Код: {res.status_code}")
                return

            self.show_message("Співробітник успішно видалений.")
            QMessageBox.information(self, "Успіх", "Співробітника видалено")
            self.load_data()
            if self.table.rowCount() == 0:
                QMessageBox.information(self, "Увага", "Сторінка порожня. Повертаємось на попередню сторінку.")
                if self.current_page>1:
                    self.current_page-=1
                    self.load_data()

        except requests.RequestException as e:
            self.show_error(f"Помилка з'єднання: {str(e)}")


    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)

    def show_message(self, message):
        QMessageBox.information(self, 'Успіх', message)
