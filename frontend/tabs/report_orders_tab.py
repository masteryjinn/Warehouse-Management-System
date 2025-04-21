import csv
import json
from datetime import timedelta
import decimal
import xml.etree.ElementTree as ET
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, QDateEdit,  QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox, QLineEdit, QLabel, QCheckBox
)
import requests
import pymysql
from user_session.current_user import CurrentUser
from styles.load_styles import load_styles
from windows.orders.chart_dialog import ReportChartDialog

def convert_decimal(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, list):
        return [convert_decimal(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_decimal(value) for key, value in obj.items()}
    return obj

class ReportWindow(QWidget):
    def __init__(self,auth_window):
        super().__init__()
        self.rows_per_page = 15
        self.current_page = 0
        self.categories = []
        self.report_data = []
        self.auth_window= auth_window

        self.setStyleSheet(load_styles())
        self.setup_ui()
        
    def showEvent(self, event):
        super().showEvent(event)
        self.load_categories()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Панель фільтрів
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Від:"))
        self.from_date = QDateEdit()
        self.from_date.setCalendarPopup(True)
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        date_layout.addWidget(self.from_date)

        date_layout.addWidget(QLabel("До:"))
        self.to_date = QDateEdit()
        self.to_date.setCalendarPopup(True)
        self.to_date.setDate(QDate.currentDate())
        date_layout.addWidget(self.to_date)

        date_layout.addWidget(QLabel("Статус:"))
        self.status_combo = QComboBox()
        self.status_map = {
            "Нові": "new",
            "Обробляються": "processing",
            "Відправлені": "shipped"
        }
        for ukr, eng in self.status_map.items():
            self.status_combo.addItem(ukr, eng)
        date_layout.addWidget(self.status_combo)

        date_layout.addWidget(QLabel("Категорія:"))
        self.category_combo = QComboBox()
        self.category_combo.addItem("Усі категорії", None)
        date_layout.addWidget(self.category_combo)

        self.generate_button = QPushButton("Сформувати звіт")
        self.generate_button.clicked.connect(self.generate_report)
        date_layout.addWidget(self.generate_button)

        layout.addLayout(date_layout)

        # Підсумок
        self.summary_label = QLabel()
        layout.addWidget(self.summary_label)


        # Таблиця звіту
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["№", "Дата", "К-сть замовлень", "К-сть товарів", "Загальний дохід"])
        layout.addWidget(self.table)

        # Пагінація
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("← Попередня")
        self.prev_button.clicked.connect(self.prev_page)
        pagination_layout.addWidget(self.prev_button)

        self.page_label = QLabel()
        pagination_layout.addWidget(self.page_label)
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_button = QPushButton("Наступна →")
        self.next_button.clicked.connect(self.next_page)
        pagination_layout.addWidget(self.next_button)

        layout.addLayout(pagination_layout)

        # Панель експорту
        export_layout = QHBoxLayout()
        self.chart_button = QPushButton("Показати графік")
        self.chart_button.clicked.connect(self.show_chart)
        self.export_format = QComboBox()
        self.export_format.addItems(["CSV", "JSON", "XML", "RDF"])
        export_layout.addWidget(self.chart_button)
        export_layout.addWidget(QLabel("Формат експорту:"))
        export_layout.addWidget(self.export_format)

        self.export_button = QPushButton("Експортувати")
        self.export_button.clicked.connect(self.export_report)
        export_layout.addWidget(self.export_button)

        layout.addLayout(export_layout)

        self.setLayout(layout)

    def next_page(self):
        self.current_page += 1
        self.update_table()

    def prev_page(self):
        self.current_page -= 1
        self.update_table()

    def update_table(self):
        start = self.current_page * self.rows_per_page
        end = start + self.rows_per_page
        page_data = self.report_data[start:end]

        self.table.setRowCount(len(page_data))
        for row_idx, row_data in enumerate(page_data):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(start + row_idx + 1)))
            self.table.setItem(row_idx, 1, QTableWidgetItem(str(row_data.get('date', ''))))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(row_data.get('total_orders', ''))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(row_data.get('total_items', ''))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(row_data.get('total_revenue', ''))))

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.verticalHeader().setDefaultSectionSize(35)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        total_pages = max(1, (len(self.report_data) - 1) // self.rows_per_page + 1)
        self.page_label.setText(f"Сторінка {self.current_page + 1} з {total_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < total_pages - 1)

    def load_categories(self):
        try:
            current_user = CurrentUser()
            token = current_user.get_token()
            res = requests.get(
                "http://localhost:8000/products/categories",
                headers={"Authorization": f"Bearer {token}"}
            )
            if res.status_code == 200:
                self.categories = res.json().get("categories", [])
                self.update_category_list()
            else:
                QMessageBox.warning(self, "Помилка", "Не вдалося отримати категорії.")
        except requests.exceptions.RequestException as req_err:
            QMessageBox.warning(self, "Помилка", f"Помилка запиту: {req_err}")

    def update_category_list(self):
        for category in self.categories:
            self.category_combo.addItem(category)

    def generate_report(self):
        start_date = self.from_date.date().toPyDate()
        end_date = self.to_date.date().toPyDate() + timedelta(days=1)
        status = self.status_combo.currentData()
        category_name = self.category_combo.currentText()
        if category_name == "Усі категорії":
            category_name = None
        current_user = CurrentUser()
        if not current_user.is_admin():
            QMessageBox.warning(self, "Увага", "У вас немає прав доступу до цієї вкладки")
            self.close()
            return
        token = current_user.get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "status": status,
            "category": category_name,
        }
        response = requests.get("http://localhost:8000/orders/report", params=params, headers=headers)

        if response.status_code == 200:
            data = response.json()  # отримуємо дані з відповіді
            self.report_data = data['data']
            print(self.report_data)  # Перевірка, що міститься в self.report_data перед експортом
            self.total_orders = data['total_orders']
            self.total_products = data['total_items']
            self.total_revenue = data['total_revenue']
            self.current_page = 0
            self.update_table()
            self.summary_label.setText(
                f"Загалом замовлень: {self.total_orders} | "
                f"Товарів: {self.total_products} | "
                f"Дохід: ₴{self.total_revenue:.2f}"
            )
        else:
            QMessageBox.warning(self, "Помилка", f"Не вдалося отримати дані. Код помилки: {response.status_code}")


    def export_report(self):
        format = self.export_format.currentText().lower()
        if not self.report_data:
            QMessageBox.warning(self, "Увага", "Немає даних для експорту.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Зберегти файл", "", f"{format.upper()} files (*.{format})")
        if not file_path:
            return

        try:
            if format == "csv":
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Дата", "К-сть замовлень", "К-сть товарів", "Загальний дохід"])
                    for row in self.report_data:
                        writer.writerow([
                            row.get("date", ""),
                            row.get("total_orders", ""),
                            row.get("total_items", ""),
                            row.get("total_revenue", "")
                        ])

            elif format == "json":
                data = [
                    {
                        "Дата": row.get("date", ""),
                        "К-сть замовлень": row.get("total_orders", ""),
                        "К-сть товарів": row.get("total_items", ""),
                        "Загальний дохід": row.get("total_revenue", "")
                    } for row in self.report_data
                ]
                data = convert_decimal(data)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)

            elif format == "xml":
                root = ET.Element("Report")
                for row in self.report_data:
                    entry = ET.SubElement(root, "Entry")
                    ET.SubElement(entry, "Date").text = str(row.get("date", ""))
                    ET.SubElement(entry, "Orders").text = str(row.get("total_orders", ""))
                    ET.SubElement(entry, "Items").text = str(row.get("total_items", ""))
                    ET.SubElement(entry, "Revenue").text = str(row.get("total_revenue", ""))
                tree = ET.ElementTree(root)
                tree.write(file_path, encoding="utf-8", xml_declaration=True)

            elif format == "rdf":
                g = Graph()
                ns = Namespace("http://example.org/report/")
                for row in self.report_data:
                    entry_uri = URIRef(ns[str(row.get("date", ""))])
                    g.add((entry_uri, RDF.type, ns.Entry))
                    g.add((entry_uri, ns.date, Literal(str(row.get("date", "")))))
                    g.add((entry_uri, ns.totalOrders, Literal(row.get("total_orders", ""))))
                    g.add((entry_uri, ns.totalItems, Literal(row.get("total_items", ""))))
                    g.add((entry_uri, ns.totalRevenue, Literal(row.get("total_revenue", ""))))
                g.serialize(destination=file_path, format="xml")

            QMessageBox.information(self, "Успіх", f"Звіт успішно експортовано у {format.upper()} формат.")

        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Сталася помилка при експорті: {str(e)}")

    def show_chart(self):
        if not self.report_data:
            QMessageBox.warning(self, "Увага", "Немає даних для побудови графіка.")
            return

        chart_dialog = ReportChartDialog(self.report_data, self)
        chart_dialog.exec()
