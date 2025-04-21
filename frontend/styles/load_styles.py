def load_styles():
    return"""
            QLabel {
                font-size: 16px;
                font-weight: bold;
                color: white;
            }
            QTableWidget {
                background-color: #34495e;
                color: #ffffff;
                border: 1px solid #2c3e50;
                font-size: 16px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: 1px solid #2c3e50;
            }
            QTableWidget::item:selected {
                background-color: #1abc9c;
                color: white;
            }
            QTableWidget::item {
                background-color: #34495e;
                color: #ffffff;
                border: 1px solid #2c3e50;
                font-size: 16px;
            }
            QPushButton {
                background-color: #1abc9c;
                color: white;
                border: 2px solid #16a085;
                border-radius: 8px;
                padding: 5px 10px;
                font-size: 16px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #16a085;
                transform: scale(1.05);
            }
            QPushButton:pressed {
                background-color: #1abc9c;
                transform: scale(0.98);
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
                color: #bdc3c7;
                border: 2px solid #7f8c8d;
            }
            QLineEdit {
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
                padding: 8px;
                font-size: 16px;
                border-radius: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #1abc9c;
            }
            QHBoxLayout {
                margin-bottom: 15px;
            }
            QVBoxLayout {
                margin: 20px;
            }
            QComboBox {
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
                padding: 6px;
                font-size: 16px;
                border-radius: 5px;
            }

            QComboBox:hover {
                border: 2px solid #1abc9c;
            }

            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #1abc9c;
                background-color: #1abc9c;
            }

            QComboBox::down-arrow {
                image: none;
                width: 0;
                height: 0;
                margin-right: 8px;
                margin-top: 6px;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white; /* Це колір стрілки */
            }

            QComboBox QAbstractItemView {
                background-color: #34495e;
                color: white;
                selection-background-color: #1abc9c;
                selection-color: white;
                border: none;
            }
            QDateEdit {
                background-color: #2c3e50;
                color: white;
                border: 2px solid #34495e;
                padding: 6px;
                font-size: 16px;
                border-radius: 5px;
            }

            QDateEdit:focus {
                border: 2px solid #1abc9c;
            }

            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px;
                border-left: 1px solid #1abc9c;
                background-color: #1abc9c;
            }

            QDateEdit::down-arrow {
                image: none;
                width: 0;
                height: 0;
                margin-right: 8px;
                margin-top: 6px;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid white;
            }

            QCheckBox {
                color: white;
                font-size: 16px;
                padding: 4px;
            }

            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }

            QCheckBox::indicator:unchecked {
                border: 2px solid #bdc3c7;
                background-color: #2c3e50;
                border-radius: 4px;
            }

            QCheckBox::indicator:checked {
                border: 2px solid #1abc9c;
                background-color: #1abc9c;
                border-radius: 4px;
            }
        """