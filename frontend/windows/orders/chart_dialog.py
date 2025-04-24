from PyQt6.QtWidgets import QDialog, QVBoxLayout, QComboBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

class ReportChartDialog(QDialog):
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Графік виторгу по днях")
        self.resize(800, 500)

        self.data = data  # Перевірка формату даних
        self.chart_type = 'line'

        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)

        self.combo_box = QComboBox()
        self.combo_box.addItems(["Лінійний графік", "Стовпчиковий графік"])
        self.combo_box.currentTextChanged.connect(self.update_chart)

        layout = QVBoxLayout()
        layout.addWidget(self.combo_box)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.draw_chart()

    def draw_chart(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Use the correct key names to access data from dictionaries
        dates = [item['date'] for item in self.data]  # Change to match your data structure
        revenues = [item['total_revenue'] for item in self.data]  # Same here for 'total_revenue'

        if self.chart_type == 'line':
            ax.plot(dates, revenues, marker='o', color='blue')
        elif self.chart_type == 'bar':
            ax.bar(dates, revenues, color='green')

        ax.set_title("Виторг по днях")
        ax.set_xlabel("Дата")
        ax.set_ylabel("Сума (грн)")
        ax.tick_params(axis='x', rotation=45)
        self.figure.tight_layout()
        self.canvas.draw()

    def update_chart(self, text):
        if text == "Лінійний графік":
            self.chart_type = 'line'
        elif text == "Стовпчиковий графік":
            self.chart_type = 'bar'
        self.draw_chart()
