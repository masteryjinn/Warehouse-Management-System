import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QMessageBox
from user_session.current_user import CurrentUser

class UpdateRoleDialog(QDialog):
    def __init__(self, employee_id, parent=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setWindowTitle("Оновити роль")
        self.setStyleSheet("""
            QWidget {
                background-color: #2F3A53;
                color: white;
                font-family: 'Arial', sans-serif;
                font-size: 12pt;
            }
            QLineEdit {
                background-color: #3C4A6B;
                border: 1px solid #607b99;
                padding: 5px;
                color: white;
            }
            QLineEdit[valid="false"] {
                border: 2px solid red;
            }
            QLineEdit[valid="true"] {
                border: 2px solid green;
            }
            QLabel.hint {
                font-size: 10pt;
                color: #FFA07A;
                margin-left: 5px;
                margin-bottom: 10px;
            }
            QComboBox {
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
        self.setLayout(QVBoxLayout())

        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "manager", "employee"])  # або з сервера
        self.layout().addWidget(QLabel("Оберіть нову роль:"))
        self.layout().addWidget(self.role_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.update_role)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

    def update_role(self):
        """Оновлює роль співробітника"""
        if not self.role_combo.currentText():
            QMessageBox.warning(self, "Помилка", "Будь ласка, виберіть роль")
            return
        current_user = CurrentUser()
        if current_user.role != "admin":
            QMessageBox.warning(self, "Помилка", "У вас немає прав для зміни ролі")
            return
        token = current_user.token
        if not token:
            QMessageBox.warning(self, "Помилка", "Вам потрібно заново увійти в систему")
            return
        new_role = self.role_combo.currentText()
        response = requests.post(
            "http://localhost:8000/employees/update_role",
            json={"employee_id": self.employee_id, "new_role": new_role},
            headers={"Authorization": f"Bearer {token}"}
        )
        if response.status_code == 200:
            QMessageBox.information(self, "Успішно", "Роль оновлено")
            self.accept()
        else:
            QMessageBox.warning(self, "Помилка", "Не вдалося оновити роль")
