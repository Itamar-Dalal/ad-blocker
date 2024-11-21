from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QIcon, QPixmap

class Styles:
    WINDOW_WIDTH = 400
    WINDOW_HEIGTH = 300
    button_style = """
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
    """
    window_title = "DNS AdBlocker"
    window_background = "background-color: white;"
    shadow_effect_color = 150, 150, 150, 150  # Semi-transparent gray
    title_style = """
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        padding: 10px;
    """
    label_style = """
        font-size: 16px;
        font-weight: bold;
        color: #2c3e50;
    """
    input_label_style = """
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
    """
    input_style = """
        QLineEdit {
            font-size: 16px;
            padding: 8px;
            border: 2px solid #2980b9;
            border-radius: 10px;
            color: black;
        }
        QLineEdit:focus {
            border: 2px solid #3498db;
        }
    """
    ICON_PATH = "icon.png"
    LOGO_PATH = "logo.png"
    LOGO_WIDTH = 125
    LOGO_HEIGTH = 125

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(Styles.window_title)
        self.setWindowIcon(QIcon(Styles.ICON_PATH))
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGTH)
        self.setStyleSheet(Styles.window_background)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(8)
        self.shadow_effect.setColor(QColor(*Styles.shadow_effect_color))
        self.shadow_effect.setOffset(2, 2)

        self.welcome_window()

    def welcome_window(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        title = QLabel("DNS AdBlocker")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(Styles.title_style)
        title.setGraphicsEffect(self.shadow_effect)
        layout.addWidget(title)

        label = QLabel("DNS-based Ad Blocker Developed By Itamar Dalal")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet(Styles.label_style)
        layout.addWidget(label)

        logo_label = QLabel()
        pixmap = QPixmap(Styles.LOGO_PATH)
        pixmap = pixmap.scaled(Styles.LOGO_WIDTH, Styles.LOGO_HEIGTH, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(logo_label)

        button = QPushButton("Connect To A Server")
        button.setStyleSheet(Styles.button_style)
        button.clicked.connect(self.connect_to_server_window)
        layout.addWidget(button)

        central_widget.setLayout(layout)

    def connect_to_server_window(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Connect to A Server")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.title_style)
        layout.addWidget(label)

        ip_label = QLabel("Server IP:")
        ip_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ip_label.setStyleSheet(Styles.input_label_style)
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("Enter server IP")
        ip_input.setStyleSheet(Styles.input_style)

        port_label = QLabel("Server Port:")
        port_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        port_label.setStyleSheet(Styles.input_label_style)
        port_input = QLineEdit()
        port_input.setPlaceholderText("Enter port number")
        port_input.setStyleSheet(Styles.input_style)

        ip_layout = QVBoxLayout()
        ip_layout.addWidget(ip_label)
        ip_layout.addWidget(ip_input)

        port_layout = QVBoxLayout()
        port_layout.addWidget(port_label)
        port_layout.addWidget(port_input)

        input_layout = QVBoxLayout()
        input_layout.addLayout(ip_layout)
        input_layout.addLayout(port_layout)
        layout.addLayout(input_layout)

        back_button = QPushButton("Connect To A Server")
        back_button.setStyleSheet(Styles.button_style)
        back_button.clicked.connect() # todo connecting to the server
        layout.addWidget(back_button)

        central_widget.setLayout(layout)

if __name__ == "__main__":
    pass
