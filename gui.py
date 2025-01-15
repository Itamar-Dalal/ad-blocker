from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QGridLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QIcon, QPixmap
from styles import Styles
from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor, QIcon, QPixmap
from styles import Styles
import client

class GUI(QMainWindow):
    def __init__(self, c: client.Client):
        super().__init__()
        self.client = c
        self.setWindowTitle(Styles.WINDOW_TITLE)
        self.setWindowIcon(QIcon(Styles.ICON_PATH))
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        self.setStyleSheet(Styles.WINDOW_BACKGROUND)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(Styles.SHADOW_BLUR_RADIUS)
        self.shadow_effect.setColor(QColor(*Styles.SHADOW_EFFECT_COLOR))
        self.shadow_effect.setOffset(*Styles.SHADOW_OFFSET)

        self.welcome_window()

    def welcome_window(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        title = QLabel("DNS AdBlocker")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(Styles.TITLE_STYLE)
        title.setGraphicsEffect(self.shadow_effect)
        layout.addWidget(title)

        label = QLabel("DNS-based Ad Blocker Developed By Itamar Dalal")
        label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        label.setStyleSheet(Styles.LABEL_STYLE)
        layout.addWidget(label)

        logo_label = QLabel()
        pixmap = QPixmap(Styles.LOGO_PATH)
        pixmap = pixmap.scaled(
            Styles.LOGO_WIDTH,
            Styles.LOGO_HEIGHT,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(logo_label)

        layout.addSpacing(Styles.LAYOUT_SPACING)

        button = QPushButton("Connect To A Server")
        button.setStyleSheet(Styles.BUTTON_STYLE)
        button.clicked.connect(self.connect_to_server_window)
        layout.addWidget(button)

        central_widget.setLayout(layout)

    def connect_to_server_window(self, error_msg=None):
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Connect to A Server")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        ip_label = QLabel("Server IP:")
        ip_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        ip_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        ip_input = QLineEdit()
        ip_input.setPlaceholderText("Enter server IP")
        ip_input.setStyleSheet(Styles.INPUT_STYLE)

        port_label = QLabel("Server Port:")
        port_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        port_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        port_input = QLineEdit()
        port_input.setPlaceholderText("Enter port number")
        port_input.setStyleSheet(Styles.INPUT_STYLE)

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

        if error_msg:
            self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 13)
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

        submit_button = QPushButton("Connect To A Server")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.connect_to_server(ip_input.text(), port_input.text()))
        layout.addWidget(submit_button)

        central_widget.setLayout(layout)

    def home_window(self):
        self.setFixedSize(Styles.HOME_WINDOW_WIDTH, Styles.HOME_WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setSpacing(Styles.LAYOUT_SPACING)

        title = QLabel("Welcome to DNS AdBlocker")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(Styles.TITLE_STYLE)
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(Styles.SHADOW_BLUR_RADIUS)
        shadow_effect.setColor(QColor(*Styles.SHADOW_COLOR))
        shadow_effect.setOffset(*Styles.SHADOW_OFFSET)
        title.setGraphicsEffect(shadow_effect)
        layout.addWidget(title)

        subtitle = QLabel("Domain Blocking and Management")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        subtitle.setStyleSheet(Styles.SUBTITLE_STYLE)
        layout.addWidget(subtitle)

        logo_label = QLabel()
        pixmap = QPixmap(Styles.LOGO_PATH)
        pixmap = pixmap.scaled(
            Styles.LOGO_WIDTH + 20,
            Styles.LOGO_HEIGHT + 20,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(logo_label)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(Styles.BUTTON_SPACING)

        buttons = [
            ("Login", self.login_window),
            ("Add Domain", self.block_domain_window),
            ("View History", self.home_window),
            ("Create Account", self.create_account_window),
            ("Delete Domain", self.home_window),
            ("More Options", self.home_window),
        ]

        row, col = 0, 0
        for button_text, callback in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet(Styles.BUTTON_STYLE)
            button.setFixedSize(Styles.BUTTON_WIDTH, Styles.BUTTON_HEIGHT)
            button.clicked.connect(callback)
            grid_layout.addWidget(button, row, col)
            row, col = divmod(row * 3 + col + 1, 3)

        centered_layout = QHBoxLayout()
        centered_layout.addStretch()
        centered_layout.addLayout(grid_layout)
        centered_layout.addStretch()

        button_widget = QWidget()
        button_widget.setLayout(centered_layout)
        button_widget.setContentsMargins(*Styles.BUTTON_MARGINS)
        layout.addWidget(button_widget)

        footer = QLabel("Developed by Itamar Dalal © 2024-2025")
        footer.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        footer.setStyleSheet(Styles.FOOTER_STYLE)
        layout.addWidget(footer)

        central_widget.setLayout(layout)

    def login_window(self, error_msg=None):
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 50)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Login")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        username_label = QLabel("Username:")
        username_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        username_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        username_input = QLineEdit()
        username_input.setPlaceholderText("Enter username")
        username_input.setStyleSheet(Styles.INPUT_STYLE)

        password_label = QLabel("Password:")
        password_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        password_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        password_input = QLineEdit()
        password_input.setPlaceholderText("Enter password")
        password_input.setStyleSheet(Styles.INPUT_STYLE)

        username_layout = QVBoxLayout()
        username_layout.addWidget(username_label)
        username_layout.addWidget(username_input)

        password_layout = QVBoxLayout()
        password_layout.addWidget(password_label)
        password_layout.addWidget(password_input)

        input_layout = QVBoxLayout()
        input_layout.addLayout(username_layout)
        input_layout.addLayout(password_layout)
        layout.addLayout(input_layout)

        if error_msg:
            self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 73)
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)

        submit_button = QPushButton("Login")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.login(username_input.text(), password_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(lambda: self.home_window())
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
    
    def block_domain_window(self):
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Block Domain")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        domain_label = QLabel("Domain:")
        domain_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        domain_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        domain_input = QLineEdit()
        domain_input.setPlaceholderText("Enter domain")
        domain_input.setStyleSheet(Styles.INPUT_STYLE)

        domain_layout = QVBoxLayout()
        domain_layout.addWidget(domain_label)
        domain_layout.addWidget(domain_input)
        layout.addLayout(domain_layout)

        submit_button = QPushButton("Block Domain")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.add_domain(domain_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(lambda: self.home_window())
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
    
    def create_account_window(self):
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Create Account")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        username_label = QLabel("Username:")
        username_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        username_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        username_input = QLineEdit()
        username_input.setPlaceholderText("Enter username")
        username_input.setStyleSheet(Styles.INPUT_STYLE)

        password_label = QLabel("Password:")
        password_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        password_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        password_input = QLineEdit()
        password_input.setPlaceholderText("Enter password")
        password_input.setEchoMode(QLineEdit.Password)
        password_input.setStyleSheet(Styles.INPUT_STYLE)

        email_label = QLabel("Email:")
        email_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        email_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter email")
        email_input.setStyleSheet(Styles.INPUT_STYLE)

        form_layout = QVBoxLayout()
        form_layout.addWidget(username_label)
        form_layout.addWidget(username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(password_input)
        form_layout.addWidget(email_label)
        form_layout.addWidget(email_input)
        layout.addLayout(form_layout)

        submit_button = QPushButton("Create Account")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.create_account(username_input.text(), password_input.text(), email_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(lambda: self.home_window())
        layout.addWidget(return_button)

        central_widget.setLayout(layout)


if __name__ == "__main__":
    pass
