from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QStackedWidget,
    QListWidgetItem, QMessageBox, QMenu, QToolButton
)
from PyQt6.QtWidgets import QSizePolicy
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize
from user_session.current_user import CurrentUser
from .home_tab import HomeTab
from windows.authorization.change_password_tab import ChangePasswordTab
from .warehouse_tab import SectionsTab
from windows.user_info.user_info_tab import UserInfoTab
from .employees_tab import EmployeesTab
from .customers_tab import CustomersTab
from .suppliers_tab import SuppliersTab
from .products_tab import ProductsTab
from .orders_tab import OrdersTab
from .stock_movements_tab import StockMovementsTab
from .report_orders_tab import ReportWindow

TOOLTIP_MAP = {
    "🏠 Головна": "Початкова сторінка системи",
    "👥 Працівники": "Керування працівниками та їх доступом",
    "🧑‍💼 Клієнти": "Перелік клієнтів та їх контактні дані",
    "🚚 Постачальники": "Інформація про постачальників товарів",
    "📦 Секції складу": "Зони та секції, де зберігаються товари",
    "📋 Перелік товарів": "Усі наявні товари на складі",
    "🧾 Замовлення": "Список замовлень і їх обробка",
    "🔄 Рух товару": "Історія переміщення товарів між секціями",
    "📊 Звіт по замовленнях": "Аналіз і статистика по замовленнях"
}


class MainWindow(QWidget):
    def __init__(self, auth_window):
        super().__init__()
        self.auth_window = auth_window
        self.setWindowTitle("Головне вікно")
        self.showFullScreen()

        current_user = CurrentUser()
        user_name = current_user.get_name()
        user_role = current_user.get_role()
        self.is_temp_password = current_user.get_is_temp_password()
        if self.is_temp_password:
            self.change_password_tab = ChangePasswordTab(self.auth_window)
            self.change_password_tab.show()

        # === ГОЛОВНИЙ МАКЕТ ===
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === ЛІВА ПАНЕЛЬ (МЕНЮ) ===
        self.menu_list = QListWidget()
        self.menu_list.setFixedWidth(250)
        self.menu_list.setStyleSheet("""
            QListWidget {
                background-color: #2c3e50;
                color: white;
                font-size: 16px;
                border: none;
            }
            QListWidget::item {
                padding: 15px;
            }
            QListWidget::item:selected {
                background-color: #1abc9c;
                font-weight: bold;
            }
        """)

        # === ВМІСТ (КОНТЕНТ) ===
        self.stack = QStackedWidget()

        # Додаємо вкладки
        self.add_tab("🏠 Головна", HomeTab())
        #self.add_tab("🔒 Змінити пароль", ChangePasswordTab())

        if user_role == "admin":
            self.add_tab("👥 Працівники", EmployeesTab(self.auth_window))
            self.add_tab("🧑‍💼 Клієнти", CustomersTab(self.auth_window))
            self.add_tab("🚚 Постачальники", SuppliersTab(self.auth_window)) 
            self.add_tab("📦 Секції складу", SectionsTab(self.auth_window))
            self.add_tab("📋 Перелік товарів", ProductsTab(self.auth_window))
            self.add_tab("🧾 Замовлення", OrdersTab(self.auth_window))
            self.add_tab("🔄 Рух товару", StockMovementsTab(self.auth_window))
            self.add_tab("📊 Звіт по замовленнях", ReportWindow(self.auth_window))
        elif user_role == "manager":
            self.add_tab("🧑‍💼 Клієнти", CustomersTab(self.auth_window))
            self.add_tab("🚚 Постачальники", SuppliersTab(self.auth_window)) 
            self.add_tab("📦 Секції складу", SectionsTab(self.auth_window))
            self.add_tab("📋 Перелік товарів", ProductsTab(self.auth_window))
            self.add_tab("🧾 Замовлення", OrdersTab(self.auth_window))
            self.add_tab("🔄 Рух товару", StockMovementsTab(self.auth_window))
        elif user_role == "employee":
            self.add_tab("📦 Секції складу", SectionsTab(self.auth_window))
            self.add_tab("📋 Перелік товарів", ProductsTab(self.auth_window))
            self.add_tab("🧾 Замовлення", OrdersTab(self.auth_window))

        # === ВЕРХНЯ ПАНЕЛЬ (ЗАГОЛОВОК + ВИХІД) ===
        header = QHBoxLayout()

        # Кнопка для приховування меню
        self.toggle_menu_button = QToolButton(self)
        self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_close.png"))
        self.toggle_menu_button.setIconSize(QSize(30, 30))
        self.toggle_menu_button.setStyleSheet("background-color: transparent; border: none;")
        self.toggle_menu_button.clicked.connect(self.toggle_menu)

        # Назва програми
        app_name_label = QLabel("Програма для управління складом")
        app_name_label.setFont(QFont("Arial", 16))
        app_name_label.setStyleSheet("color: white;")

        # Кнопка користувача з випадаючим меню
        self.user_button = QToolButton(self)
        self.user_button.setText(f"{user_name} ({user_role.capitalize()})")
        self.user_button.setIcon(QIcon("frontend/icons/user_icon.png"))
        self.user_button.setStyleSheet("color: white; background-color: #34495e; padding: 10px; border-radius: 5px;")
        self.user_button.setFont(QFont("Arial", 14))
        self.user_button.setIconSize(QSize(40, 40))
        self.user_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.user_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.user_button.clicked.connect(self.show_user_menu)

        header.addWidget(self.toggle_menu_button)
        header.addWidget(app_name_label)
        header.addWidget(self.user_button)

        top_panel = QWidget()
        top_panel.setLayout(header)
        top_panel.setStyleSheet("background-color: #34495e; padding: 10px;")

        # === ОСНОВНИЙ КОНТЕЙНЕР ===
        content_layout = QVBoxLayout()
        content_layout.addWidget(top_panel)
        content_layout.addWidget(self.stack)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)    
        content_layout.setStretch(0, 1)
        content_layout.setStretch(1, 10)

        main_layout.addWidget(self.menu_list)
        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

        # Aдаптивне поведінка для вмісту
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.menu_list.currentRowChanged.connect(self.stack.setCurrentIndex)


    def toggle_menu(self):
        """Приховує або показує меню"""
        if self.menu_list.isVisible():
            self.menu_list.setVisible(False)
            self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_open.png"))
        else:
            self.menu_list.setVisible(True)
            self.toggle_menu_button.setIcon(QIcon("frontend/icons/menu_close.png"))

    def add_tab(self, name, widget):
        """Додає вкладку в меню та контент з кастомною підказкою"""
        item = QListWidgetItem(name)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        tooltip_text = TOOLTIP_MAP.get(name, name)
        item.setToolTip(tooltip_text)
        self.menu_list.addItem(item)
        self.stack.addWidget(widget)

    def logout(self):
        """Діалогове вікно для виходу"""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Вихід")
        msg_box.setText("Ви хочете вийти з акаунту чи закрити програму?")
        
        # Стиль для всього вікна повідомлення
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #2F3A53;
                color: white;
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
            }
            QMessageBox QLabel {
                font-size: 14pt;
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
            QPushButton:focus {
                outline: none;
            }
        """)

        logout_account_btn = msg_box.addButton("Вийти з акаунту", QMessageBox.ButtonRole.YesRole)
        exit_app_btn = msg_box.addButton("Вийти з програми", QMessageBox.ButtonRole.NoRole)
        cancel_btn = msg_box.addButton("Скасувати", QMessageBox.ButtonRole.RejectRole)

        msg_box.exec()

        if msg_box.clickedButton() == logout_account_btn:
            self.close()
            self.auth_window.show()
        elif msg_box.clickedButton() == exit_app_btn:
            self.close()
            exit()

    def show_user_menu(self):
        """Відкриває випадаюче меню користувача"""
        user_menu = QMenu(self)

        personal_info_action = user_menu.addAction("Особиста інформація")
        change_password_action = user_menu.addAction("Змінити пароль")
        logout_action = user_menu.addAction("Вийти")

        user_menu.setStyleSheet("""
            QMenu {
                font-size: 14px;
                font-weight: bold;
                color: white;
                background-color: #34495e;
            }
            QMenu::item {
                padding: 5px 10px;
                background-color: #34495e;
                color: white;
            }
            QMenu::item:selected {
                background-color: #1abc9c;
                color: grey;
            }
        """)

        personal_info_action.triggered.connect(self.open_personal_info)
        change_password_action.triggered.connect(self.open_change_password_tab)
        logout_action.triggered.connect(self.logout)

        user_menu.exec(self.user_button.mapToGlobal(self.user_button.rect().bottomLeft()))

    def open_personal_info(self):
        """Відкриває вікно з особистою інформацією"""
        self.personal_info_window = UserInfoTab(self.auth_window)  # Відкриваємо вкладку з особистою інформацією
        self.personal_info_window.show()

    def open_change_password_tab(self):
        """Відкриває вкладку з налаштуваннями (змінити пароль)"""
        self.change_password_tab = ChangePasswordTab(self.auth_window)  # Відкриваємо вкладку з налаштуваннями
        self.change_password_tab.show()
