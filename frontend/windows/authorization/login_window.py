import requests
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QMessageBox, QInputDialog, QCheckBox
from tabs.main_window import MainWindow
from user_session.current_user import CurrentUser  # Імпортуємо об'єкт current_user
from config.config import API_URL  # Імпортуємо API_URL з конфігурації

class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Авторизація')
        self.setGeometry(100, 100, 300, 200)  # Збільшимо висоту для більшого простору

        # Додаємо стиль для всього вікна
        self.setStyleSheet("""
            QWidget {
                background-color: #2F3A53;  /* Темно-синій фон */
                color: white;  /* Білий колір тексту */
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
            }
            QLabel {
                font-size: 14pt;
                margin-bottom: 5px;
            }
            QLineEdit {
                background-color: #3C4A6B;  /* Темно-синій фон для полів введення */
                border: 1px solid #607b99;  /* Світло-сині рамки */
                padding: 5px;
                color: white;
            }
            QPushButton {
                background-color: #557A95;  /* Світло-синій фон кнопок */
                color: white;
                border-radius: 5px;
                padding: 10px;
                font-size: 12pt;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #4A6581;  /* Темніший колір при наведенні */
            }
            QCheckBox {
                color: white;
                font-size: 12pt;
            }
        """)

        self.layout = QVBoxLayout()

        self.username_label = QLabel('Ім\'я користувача')
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_label)
        self.layout.addWidget(self.username_input)

        self.password_label = QLabel('Пароль')
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # За замовчуванням пароль прихований
        self.layout.addWidget(self.password_label)
        self.layout.addWidget(self.password_input)

        # Створюємо квадратик для перемикання видимості пароля
        self.show_password_checkbox = QCheckBox('Показати пароль')
        self.show_password_checkbox.stateChanged.connect(self.toggle_password_visibility)
        self.layout.addWidget(self.show_password_checkbox)

        self.login_button = QPushButton('Увійти')
        self.login_button.clicked.connect(self.login)
        self.layout.addWidget(self.login_button)

        self.forgot_password_button = QPushButton('Забули пароль?')
        self.forgot_password_button.clicked.connect(self.forgot_password)
        self.layout.addWidget(self.forgot_password_button)

        self.setLayout(self.layout)

    def toggle_password_visibility(self):
        """Перемикає видимість пароля"""
        if self.show_password_checkbox.isChecked():
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)  # Показуємо пароль
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)  # Приховуємо пароль
        
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        response = requests.post(f"{API_URL}/login/", json={"username": username, "password": password})
        
        if response.status_code == 200:
            data = response.json()
            print(data)  # Виводимо дані для налагодження
            
            token = data["token"]
            role = data["role"]
            is_temp_password = data["is_temp_password"]
            if is_temp_password:
                QMessageBox.warning(self, "Попередження", "Ви використовуєте тимчасовий пароль. Будь ласка, змініть його, щоб забезпечити безпеку вашого акаунту та отримати доступ до інформації.")
            
            # Ініціалізуємо CurrentUser та зберігаємо необхідні дані
            current_user = CurrentUser()
            current_user.set_user_data(username, role, token,is_temp_password)

            self.username_input.clear()
            self.password_input.clear()
            
            self.show_main_app()
        else:
            self.show_error("Невірний логін або пароль!")
            #self.username_input.clear()
            self.password_input.clear()


    def forgot_password(self):
        email, ok = self.get_email_from_user()
        if ok:
            # Відправка запиту на відновлення пароля
            response = requests.post(f"{API_URL}/reset-password/", json={"email": email})
            
            if response.status_code == 200:
                # Отримуємо дані з відповіді
                data = response.json()
                temp_password = data.get("temp_password", None)  # Отримуємо тимчасовий пароль

                # Якщо тимчасовий пароль отриманий
                if temp_password:
                    # Відображаємо повідомлення з паролем
                    QMessageBox.information(self, "Відновлення пароля", f"Тимчасовий пароль: {temp_password}\nВін надіслано на вашу пошту.")
                else:
                    self.show_error("Не вдалося отримати тимчасовий пароль.")
            else:
                self.show_error("Користувача з таким email не знайдено.")


    def get_email_from_user(self):
        email_input, ok = QInputDialog.getText(self, 'Введіть email', 'Введіть ваш email:')
        return email_input, ok

    def show_main_app(self):
        self.close()
        self.main_window = MainWindow(self)  
        self.main_window.show()  
        print('Вхід успішний!')

    def show_error(self, message):
        QMessageBox.critical(self, 'Помилка', message)
