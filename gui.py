from PyQt6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Beautiful PyQt6 App")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: white;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        self.label = QLabel("Welcome to PyQt6!")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(8)
        shadow_effect.setColor(QColor(150, 150, 150, 150))  # Semi-transparent gray
        shadow_effect.setOffset(2, 2)
        self.label.setGraphicsEffect(shadow_effect)

        layout.addWidget(self.label)

        button = QPushButton("Click Me!")
        button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-size: 18px;
                font-weight: bold;
                border-radius: 15px;
                padding: 10px 20px;
                border: 2px solid #2980b9;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1e6f98;
                border: 2px solid #145374;
            }
        """)
        button.clicked.connect(self.on_button_click)
        layout.addWidget(button)

        central_widget.setLayout(layout)

    def on_button_click(self):
        self.label.setText("Thank you for clicking!")
        self.label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
            padding: 10px;
        """)


if __name__ == "__main__":
    pass
