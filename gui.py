__author__ = "Itamar Dalal"

import logging
from PyQt6.QtWidgets import QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLineEdit, QGridLayout, QHBoxLayout, QCheckBox, QToolButton, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGraphicsDropShadowEffect, QApplication
from PyQt6.QtGui import QColor, QIcon, QPixmap
from styles import Styles
from registry import RegistryHandler
from typing import Any
from dns_config import DNSConfig
from datetime import datetime
from settings import Settings
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QTableWidgetItem

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GUI(QMainWindow):
    LIGHT_THEME = RegistryHandler.LIGHT_THEME
    DARK_THEME = RegistryHandler.DARK_THEME
    DEFAULT_THEME = 2

    def __init__(self, c: Any) -> None:
        """Initialize the GUI and set up the initial window."""
        super().__init__()
        self.client = c
        self.setWindowTitle(Styles.WINDOW_TITLE)
        self.setWindowIcon(GUI.get_app_icon())
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        self.shadow_effect = QGraphicsDropShadowEffect()
        self.shadow_effect.setBlurRadius(Styles.SHADOW_BLUR_RADIUS)
        self.shadow_effect.setColor(QColor(*Styles.SHADOW_EFFECT_COLOR))
        self.shadow_effect.setOffset(*Styles.SHADOW_OFFSET)
        self.update_theme(2)
        self.welcome_window()
        self.logged_in = False

    @staticmethod
    def get_app_icon() -> QIcon:
        """Return the application icon."""
        icon = QIcon(Styles.ICON_PATH)
        if not icon.isNull():
            return icon
        else:
            logger.warning(f"Could not load icon from {Styles.ICON_PATH}")
            return QIcon()  # Return empty icon as fallback
    
    def change_logged_in_status(self, logged_in: bool) -> None:
        """Update the logged-in status and notify via logger."""
        self.logged_in = logged_in
        logger.info(f"Logged-in status changed to: {self.logged_in}")
    
    def welcome_window(self):
        """Display the welcome window."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        title = QLabel("DNS AdBlocker")
        title.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        title.setStyleSheet(Styles.TITLE_STYLE)
        
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(Styles.SHADOW_BLUR_RADIUS)
        shadow_effect.setColor(QColor(*Styles.SHADOW_EFFECT_COLOR))
        shadow_effect.setOffset(*Styles.SHADOW_OFFSET)
        title.setGraphicsEffect(shadow_effect)
        
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
        logger.info("Navigated to Welcome Window")

    def connect_to_server_window(self, error_msg=None):
        """Display the window for connecting to a server, optionally showing an error message."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 120 if error_msg else Styles.WINDOW_HEIGHT + 90)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Connect To A Server")
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
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in connect_to_server_window: {error_msg}")

        submit_button = QPushButton("Connect To A Server")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.connect_to_server(ip_input.text(), port_input.text()))
        layout.addWidget(submit_button)

        # --- Add Find Server in LAN Button ---
        find_server_button = QPushButton("Find Server in LAN")
        find_server_button.setStyleSheet(Styles.BUTTON_STYLE)
        find_server_button.clicked.connect(lambda: self.client.find_server_in_lan())
        layout.addWidget(find_server_button)
        # --------------------------------------

        return_button = QPushButton("Return To Welcome Window")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.welcome_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Connect To Server Window")

    def home_window(self):
        """Display the main home window once logged in."""
        self.setFixedSize(Styles.WINDOW_WIDTH + 375, Styles.WINDOW_HEIGHT + 300)
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

        label_grid = QGridLayout()
        label_grid.setContentsMargins(0, 0, 0, 0)
        label_grid.setHorizontalSpacing(0)

        try:
            username = self.client.get_current_username()
        except Exception:
            username = "guest"
        hello_label = QLabel(f"Hello <span style='color:#3498db;'>{username}</span>")
        hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        hello_label.setStyleSheet(Styles.HELLO_STYLE)
        hello_label.setFixedHeight(30)
        label_grid.addWidget(hello_label, 0, 0, 1, 1)

        subtitle = QLabel("Domain Blocking and Management")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter)
        subtitle.setStyleSheet(Styles.SUBTITLE_STYLE)
        subtitle.setFixedHeight(30)
        label_grid.addWidget(subtitle, 0, 1, 1, 1, Qt.AlignmentFlag.AlignHCenter)

        label_grid.setColumnStretch(0, 1)
        label_grid.setColumnStretch(1, 2)
        label_grid.setColumnStretch(2, 1)

        layout.addLayout(label_grid)

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
            ("Login", self.login_window, True),
            ("Block Domain", self.block_domain_window, False),
            ("View History", self.history_window, False),
            ("Create Account", self.create_account_window, True),
            ("Unblock Domain", self.unblock_domain_window, False),
            ("Admin Panel", self.admin_panel_window, False),
            ("Connect To DNS", self.connect_to_dns_window),
            ("Settings", self.settings_window),
            ("Exit", QApplication.instance().quit),
        ]

        row, col = 0, 0
        for button_text, callback, *enabled in buttons:
            button = QPushButton(button_text)
            button.setStyleSheet(Styles.BUTTON_STYLE)
            button.setFixedSize(Styles.BUTTON_WIDTH, Styles.BUTTON_HEIGHT)
            # Use Settings.ADMIN_USERNAME.value for admin check
            if (not self.logged_in and enabled and not enabled[0]) or \
               (self.logged_in and enabled and enabled[0]) or \
               (self.logged_in and button_text == "Admin Panel" and username != f"{Settings.ADMIN_USERNAME.value} (admin)"):
                button.setEnabled(False)
                button.setStyleSheet(Styles.DISABLED_BUTTON_STYLE)
                button.enterEvent = lambda event: QApplication.setOverrideCursor(Qt.CursorShape.ForbiddenCursor)
                button.leaveEvent = lambda event: QApplication.restoreOverrideCursor()
            else:
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
        logger.info("Navigated to Home Window")

    def login_window(self, error_msg=None):
        """Display the login window with an optional error message."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 180 if error_msg else Styles.WINDOW_HEIGHT + 150)
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
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        toggle_password_button = QToolButton()
        toggle_password_button.setIcon(QIcon(Styles.EYE_ICON_PATH))
        toggle_password_button.setCheckable(True)
        toggle_password_button.setStyleSheet(Styles.TOGGLE_BUTTON_STYLE)
        toggle_password_button.clicked.connect(lambda: self.toggle_password_visibility(password_input, toggle_password_button))

        password_layout = QHBoxLayout()
        password_layout.addWidget(password_input)
        password_layout.addWidget(toggle_password_button)

        username_layout = QVBoxLayout()
        username_layout.addWidget(username_label)
        username_layout.addWidget(username_input)

        input_layout = QVBoxLayout()
        input_layout.addLayout(username_layout)
        input_layout.addWidget(password_label)
        input_layout.addLayout(password_layout)
        layout.addLayout(input_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in login_window: {error_msg}")

        submit_button = QPushButton("Login")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.login(username_input.text(), password_input.text()))
        layout.addWidget(submit_button)
        
        register_button = QPushButton("Don't have an account? Register")
        register_button.setStyleSheet(Styles.BUTTON_STYLE)
        register_button.clicked.connect(self.create_account_window)
        layout.addWidget(register_button)

        forgot_button = QPushButton("Forgot password? Reset")
        forgot_button.setStyleSheet(Styles.BUTTON_STYLE)
        forgot_button.clicked.connect(self.forgot_password_window)
        layout.addWidget(forgot_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Login Window")

    def forgot_password_window(self, error_msg=None):
        """Display the forgot password window, optionally with an error message."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Forgot Password")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        email_label = QLabel("Email:")
        email_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        email_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter your email")
        email_input.setStyleSheet(Styles.INPUT_STYLE)

        email_layout = QVBoxLayout()
        email_layout.addWidget(email_label)
        email_layout.addWidget(email_input)
        layout.addLayout(email_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in forgot_password_window: {error_msg}")

        submit_button = QPushButton("Send Code")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.forgot_password(email_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return to Login")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.login_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Forgot Password Window")
    
    def forgot_password_code_window(self, error_msg=None):
        """Display the forgotten password code verification window."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Reset Password")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        code_label = QLabel("Code:")
        code_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        code_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        code_input = QLineEdit()
        code_input.setPlaceholderText("Enter verification code")
        code_input.setStyleSheet(Styles.INPUT_STYLE)

        code_layout = QVBoxLayout()
        code_layout.addWidget(code_label)
        code_layout.addWidget(code_input)
        layout.addLayout(code_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in forgot_password_code_window: {error_msg}")
        
        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.forgot_password_code(code_input.text()))
        layout.addWidget(submit_button)

        again_button = QPushButton("Didn't receive a code? Try again")
        again_button.setStyleSheet(Styles.BUTTON_STYLE)
        again_button.clicked.connect(self.forgot_password_window)
        layout.addWidget(again_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Forgot Password Code Window")
    
    def reset_password_window(self, error_msg=None):
        """Display the reset password window for entering a new password."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT - 70 if error_msg else Styles.WINDOW_HEIGHT - 90)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Reset Password")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        password_label = QLabel("New Password:")
        password_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        password_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        password_input = QLineEdit()
        password_input.setPlaceholderText("Enter new password")
        password_input.setStyleSheet(Styles.INPUT_STYLE)
        password_input.setEchoMode(QLineEdit.EchoMode.Password)

        toggle_password_button = QToolButton()
        toggle_password_button.setIcon(QIcon(Styles.EYE_ICON_PATH))
        toggle_password_button.setCheckable(True)
        toggle_password_button.setStyleSheet(Styles.TOGGLE_BUTTON_STYLE)  # Apply white background style
        toggle_password_button.clicked.connect(lambda: self.toggle_password_visibility(password_input, toggle_password_button))

        password_layout = QHBoxLayout()
        password_layout.addWidget(password_input)
        password_layout.addWidget(toggle_password_button)
        layout.addLayout(password_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in reset_password_window: {error_msg}")

        submit_button = QPushButton("Submit")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.reset_password(password_input.text()))
        layout.addWidget(submit_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Reset Password Window")
    
    def change_password_window(self, error_msg=None):
        """Display the change password window for sending a verification code."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Change Password")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        email_label = QLabel("Email:")
        email_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        email_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        email_input = QLineEdit()
        email_input.setPlaceholderText("Enter your email")
        email_input.setStyleSheet(Styles.INPUT_STYLE)

        email_layout = QVBoxLayout()
        email_layout.addWidget(email_label)
        email_layout.addWidget(email_input)
        layout.addLayout(email_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in change_password_window: {error_msg}")

        submit_button = QPushButton("Send Code")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.forgot_password(email_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return to Settings")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.settings_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Change Password Window")
    
    def block_domain_window(self, error_msg=None):
        """Display the window to block a domain with an optional error message."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT if not error_msg else Styles.WINDOW_HEIGHT - 10)
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

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in block_domain_window: {error_msg}")

        submit_button = QPushButton("Block Domain")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.block_domain(domain_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Block Domain Window")
    
    def create_account_window(self, error_msg=None):
        """Display the account creation window with an optional error message."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 220 if error_msg else Styles.WINDOW_HEIGHT + 170)
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
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setStyleSheet(Styles.INPUT_STYLE)

        toggle_password_button = QToolButton()
        toggle_password_button.setIcon(QIcon(Styles.EYE_ICON_PATH))
        toggle_password_button.setCheckable(True)
        toggle_password_button.setStyleSheet(Styles.TOGGLE_BUTTON_STYLE)
        toggle_password_button.clicked.connect(lambda: self.toggle_password_visibility(password_input, toggle_password_button))

        password_layout = QHBoxLayout()
        password_layout.addWidget(password_input)
        password_layout.addWidget(toggle_password_button)

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
        form_layout.addLayout(password_layout)
        form_layout.addWidget(email_label)
        form_layout.addWidget(email_input)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            form_layout.addWidget(error_label)
            logger.error(f"Error in create_account_window: {error_msg}")

        layout.addLayout(form_layout)

        submit_button = QPushButton("Create Account")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.create_account(username_input.text(), password_input.text(), email_input.text()))
        layout.addWidget(submit_button)

        login_button = QPushButton("Already have an account? Login")
        login_button.setStyleSheet(Styles.BUTTON_STYLE)
        login_button.clicked.connect(self.login_window)
        layout.addWidget(login_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Create Account Window")

    def email_verification_window(self, error_msg=None):
        """Display the email verification window for new account setup."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT if error_msg else Styles.WINDOW_HEIGHT - 30)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Email Verification")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        code_label = QLabel("Verification Code:")
        code_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        code_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        code_input = QLineEdit()
        code_input.setPlaceholderText("Enter verification code")
        code_input.setStyleSheet(Styles.INPUT_STYLE)

        code_layout = QVBoxLayout()
        code_layout.addWidget(code_label)
        code_layout.addWidget(code_input)
        layout.addLayout(code_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in email_verification_window: {error_msg}")

        submit_button = QPushButton("Submit Code")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.verify_email(code_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Didn't receive a code? Try again")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.create_account_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Email Verification Window")
    
    def unblock_domain_window(self, error_msg=None):
        """Display the window to unblock a previously blocked domain."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT if not error_msg else Styles.WINDOW_HEIGHT - 10)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Unblock Domain")
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

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in unblock_domain_window: {error_msg}")

        submit_button = QPushButton("Unblock Domain")
        submit_button.setStyleSheet(Styles.BUTTON_STYLE)
        submit_button.clicked.connect(lambda: self.client.unblock_domain(domain_input.text()))
        layout.addWidget(submit_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Unblock Domain Window")
    
    def connect_to_dns_window(self, error_msg=None):
        """Display the window to connect to a DNS server, optionally with error info."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT + 145 if error_msg else Styles.WINDOW_HEIGHT + 105)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Connect to DNS")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        dns_ip_label = QLabel("DNS IP:")
        dns_ip_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        dns_ip_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        self.dns_ip_input = QLineEdit()
        self.dns_ip_input.setPlaceholderText("Enter DNS IP")
        self.dns_ip_input.setStyleSheet(Styles.INPUT_STYLE)

        interface_label = QLabel("Select Interface:")
        interface_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        interface_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        interface_dropdown = QComboBox()
        interface_dropdown.addItems(DNSConfig.get_network_interfaces())
        interface_dropdown.setPlaceholderText("Select interface")
        interface_dropdown.setStyleSheet(Styles.DROPDOWN_STYLE)

        dns_ip_layout = QVBoxLayout()
        dns_ip_layout.addWidget(dns_ip_label)
        dns_ip_layout.addWidget(self.dns_ip_input)

        interface_layout = QVBoxLayout()
        interface_layout.addWidget(interface_label)
        interface_layout.addWidget(interface_dropdown)

        input_layout = QVBoxLayout()
        input_layout.addLayout(dns_ip_layout)
        input_layout.addLayout(interface_layout)
        layout.addLayout(input_layout)

        layout.addSpacing(Styles.LAYOUT_SPACING)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in connect_to_dns_window: {error_msg}")
        
        connect_button = QPushButton("Connect to DNS")
        connect_button.setStyleSheet(Styles.BUTTON_STYLE)
        connect_button.clicked.connect(lambda: self.client.connect_to_dns(interface_dropdown.currentText(), self.dns_ip_input.text()))
        layout.addWidget(connect_button)

        # Add Find DNS in LAN button
        find_dns_button = QPushButton("Find DNS in LAN")
        find_dns_button.setStyleSheet(Styles.BUTTON_STYLE)
        find_dns_button.clicked.connect(lambda: self.client.find_dns_in_lan(interface_dropdown.currentText()))
        layout.addWidget(find_dns_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Connect to DNS Window")

    def update_dns_ip_field(self, dns_ip):
        """Update the DNS IP input field with the given IP address."""
        self.dns_ip_input.setText(dns_ip)

    def admin_panel_window(self, error_msg=None):
        """Display the admin panel window with optional error information."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Admin Panel")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        admin_logo_label = QLabel()
        admin_logo_pixmap = QPixmap("assets/images/admin_logo.png")
        admin_logo_pixmap = admin_logo_pixmap.scaled(160, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        admin_logo_label.setPixmap(admin_logo_pixmap)
        admin_logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(admin_logo_label)

        button_layout = QHBoxLayout()
        users_button = QPushButton("Users Table")
        users_button.setStyleSheet(Styles.BUTTON_STYLE)
        users_button.clicked.connect(self.show_users_table)
        button_layout.addWidget(users_button)

        domains_button = QPushButton("Domains Table")
        domains_button.setStyleSheet(Styles.BUTTON_STYLE)
        domains_button.clicked.connect(self.show_domains_table)
        button_layout.addWidget(domains_button)

        layout.addLayout(button_layout)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in admin_panel_window: {error_msg}")

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Admin Panel Window")

    def load_domains_in_chunks(self, table, domains, search_button=None, return_button=None, is_history_window=False):
        """Load domains into the table in chunks using QTimer to avoid UI freezing."""
        if search_button:
            search_button.setEnabled(False)
            search_button.setText("Loading...")
            search_button.setStyleSheet(Styles.DISABLED_BUTTON_STYLE)
        if return_button:
            return_button.setEnabled(False)
            return_button.setText("Loading...")
            return_button.setStyleSheet(Styles.DISABLED_BUTTON_STYLE)

        chunk_size = Settings.CHUNK_SIZE.value
        delay_ms = int(Settings.LOADING_DELAY.value * 1000)  # QTimer uses milliseconds
        index = {'i': 0}  # Use mutable container to keep track inside nested function

        def load_chunk():
            i = index['i']
            if i >= len(domains):
                if search_button:
                    search_button.setEnabled(True)
                    search_button.setText("Search")
                    search_button.setStyleSheet(Styles.BUTTON_STYLE)
                if return_button:
                    return_button.setEnabled(True)
                    return_button.setText("Return To Admin Panel" if not is_history_window else "Return Home")
                    return_button.setStyleSheet(Styles.BUTTON_STYLE)
                return

            chunk = domains[i:i + chunk_size]
            current_row = table.rowCount()
            table.setRowCount(current_row + len(chunk))

            for row, domain_data in enumerate(chunk, start=current_row):
                for col, data in enumerate(domain_data):
                    table.setItem(row, col, QTableWidgetItem(str(data)))

            index['i'] += chunk_size
            QTimer.singleShot(delay_ms, load_chunk)

        load_chunk()


    def search_domain_in_table(self, table, domain_to_search: str, column: int = 0) -> None:
        """Search for a domain in the specified table and highlight it"""
        if not domain_to_search:
            logger.warning("Search input is empty")
            return
        for row in range(table.rowCount()):
            if table.item(row, column) and table.item(row, column).text() == domain_to_search:
                table.selectRow(row)
                table.scrollToItem(table.item(row, column), QAbstractItemView.ScrollHint.PositionAtCenter)
                logger.info(f"Domain '{domain_to_search}' found at row {row}")
                return
        logger.warning(f"Domain '{domain_to_search}' not found in the table")

    def show_domains_table(self):
        """Show the domains table in the admin panel."""
        self.setFixedSize(Styles.WINDOW_WIDTH + 600, Styles.WINDOW_HEIGHT + 300)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Domains Table")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search Domain:")
        search_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter domain name")
        search_input.setStyleSheet(Styles.INPUT_STYLE)
        search_button = QPushButton("Search")
        search_button.setStyleSheet(Styles.BUTTON_STYLE)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Domain", "Username", "Time Added", "Source", "Currently Blocked"])
        table.setStyleSheet(Styles.TABLE_STYLE)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        return_button = QPushButton("Return To Admin Panel")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.admin_panel_window)
        
        domains = self.client.get_all_domains()
        self.load_domains_in_chunks(table, domains, search_button, return_button, False)

        search_button.clicked.connect(lambda: self.search_domain_in_table(table, search_input.text()))

        layout.addWidget(table)

        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Domains Table in Admin Panel")

    def show_users_table(self):
        """Show the users table in the admin panel."""
        self.setFixedSize(Styles.WINDOW_WIDTH + 600, Styles.WINDOW_HEIGHT + 300)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Users Table")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search User:")
        search_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter username")
        search_input.setStyleSheet(Styles.INPUT_STYLE)
        search_button = QPushButton("Search")
        search_button.setStyleSheet(Styles.BUTTON_STYLE)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Username", "Email", "Password Hash", "Salt", "Delete"])
        table.setStyleSheet(Styles.TABLE_STYLE)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        users = self.client.get_all_users()

        table.setRowCount(len(users))
        for row, (username, email, password, salt) in enumerate(users):
            # Username column
            if username == Settings.ADMIN_USERNAME.value:
                username_display = f"{username} (admin)"
            else:
                username_display = username
            table.setItem(row, 0, QTableWidgetItem(username_display))
            table.setItem(row, 1, QTableWidgetItem(email))
            table.setItem(row, 2, QTableWidgetItem(password))
            table.setItem(row, 3, QTableWidgetItem(salt))

            delete_btn = QPushButton("")
            if username == Settings.ADMIN_USERNAME.value:
                delete_btn.setEnabled(False)
                delete_btn.setStyleSheet(Styles.DISABLED_BUTTON_STYLE)
                delete_btn.enterEvent = lambda event: QApplication.setOverrideCursor(Qt.CursorShape.ForbiddenCursor)
                delete_btn.leaveEvent = lambda event: QApplication.restoreOverrideCursor()
            else:
                delete_btn.setStyleSheet(Styles.DELETE_BUTTON_STYLE)
                # Use lambda with default argument to capture username
                delete_btn.clicked.connect(lambda _, uname=username: self.delete_user_from_server(uname))
            table.setCellWidget(row, 4, delete_btn)

        search_button.clicked.connect(lambda: self.search_domain_in_table(table, search_input.text()))

        layout.addWidget(table)

        return_button = QPushButton("Return To Admin Panel")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.admin_panel_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Users Table in Admin Panel")

    def delete_user_from_server(self, username):
        """Request deletion of a user from the server."""
        self.client.delete_user(username)
        self.show_users_table()

    def settings_window(self):
        """Display the settings window."""
        self.setFixedSize(Styles.WINDOW_WIDTH, Styles.WINDOW_HEIGHT)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Settings")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        change_theme_button = QPushButton("Change Theme")
        change_theme_button.setStyleSheet(Styles.BUTTON_STYLE)
        change_theme_button.clicked.connect(lambda: self.change_theme_window())
        layout.addWidget(change_theme_button)

        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet(Styles.BUTTON_STYLE)
        if not self.logged_in:
            logout_button.setEnabled(False)
            logout_button.setStyleSheet(Styles.DISABLED_BUTTON_STYLE)
            logout_button.enterEvent = lambda event: QApplication.setOverrideCursor(Qt.CursorShape.ForbiddenCursor)
            logout_button.leaveEvent = lambda event: QApplication.restoreOverrideCursor()
        else:
            logout_button.clicked.connect(self.client.logout)
        layout.addWidget(logout_button)

        change_password_button = QPushButton("Change Password")
        change_password_button.setStyleSheet(Styles.BUTTON_STYLE)
        change_password_button.clicked.connect(self.change_password_window)
        layout.addWidget(change_password_button)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Settings Window")

    def change_theme_window(self):
        """Display the theme change window."""
        self.setFixedSize(Styles.WINDOW_WIDTH + 600, Styles.WINDOW_HEIGHT + 200)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("Change Theme")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        theme_layout = QHBoxLayout()

        light_mode_button = QPushButton()
        light_mode_pixmap = QPixmap(Styles.LIGHT_MODE_IMAGE_PATH).scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
        light_mode_button.setIcon(QIcon(light_mode_pixmap))
        light_mode_button.setIconSize(light_mode_pixmap.size())
        light_mode_button.setStyleSheet(Styles.BUTTON_STYLE)
        light_mode_button.clicked.connect(lambda: self.update_theme(GUI.LIGHT_THEME))
        theme_layout.addWidget(light_mode_button)

        dark_mode_button = QPushButton()
        dark_mode_pixmap = QPixmap(Styles.DARK_MODE_IMAGE_PATH).scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio)
        dark_mode_button.setIcon(QIcon(dark_mode_pixmap))
        dark_mode_button.setIconSize(dark_mode_pixmap.size())
        dark_mode_button.setStyleSheet(Styles.BUTTON_STYLE)
        dark_mode_button.clicked.connect(lambda: self.update_theme(GUI.DARK_THEME))
        theme_layout.addWidget(dark_mode_button)

        layout.addLayout(theme_layout)

        return_button = QPushButton("Return To Settings")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.settings_window)
        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to Change Theme Window")
    
    def history_window(self, error_msg=None):
        """Display the history window for viewing blocked domains."""
        self.setFixedSize(Styles.WINDOW_WIDTH + 200, Styles.WINDOW_HEIGHT + 250)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        label = QLabel("History")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(Styles.TITLE_STYLE)
        layout.addWidget(label)

        search_layout = QHBoxLayout()
        search_label = QLabel("Search Domain:")
        search_label.setStyleSheet(Styles.INPUT_LABEL_STYLE)
        search_input = QLineEdit()
        search_input.setPlaceholderText("Enter domain name")
        search_input.setStyleSheet(Styles.INPUT_STYLE)
        search_button = QPushButton("Search")
        search_button.setStyleSheet(Styles.BUTTON_STYLE)
        search_layout.addWidget(search_label)
        search_layout.addWidget(search_input)
        search_layout.addWidget(search_button)
        layout.addLayout(search_layout)

        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Blocked Domain", "Time Added", "Currently Blocked"])
        table.setStyleSheet(Styles.TABLE_STYLE)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        return_button = QPushButton("Return Home")
        return_button.setStyleSheet(Styles.BUTTON_STYLE)
        return_button.clicked.connect(self.home_window)

        try:
            blocked_domains = self.client.get_blocked_domains()
            formatted_domains = []
            for domain, time_added, currently_blocked in blocked_domains:
                try:
                    readable_time = datetime.fromtimestamp(float(time_added)).strftime('%Y-%m-%d %H:%M:%S')
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to convert time_added '{time_added}' to human-readable format: {e}")
                    readable_time = time_added
                formatted_domains.append((domain, readable_time, "Yes" if int(currently_blocked) else "No"))
            
            self.load_domains_in_chunks(table, formatted_domains, search_button, return_button, True)
        except Exception as e:
            logger.error(f"Failed to retrieve blocked domains: {e}")
            error_label = QLabel("Failed to load blocked domains.")
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            layout.addWidget(error_label)

        search_button.clicked.connect(lambda: self.search_domain_in_table(table, search_input.text()))

        layout.addWidget(table)

        if error_msg:
            error_label = QLabel(error_msg)
            error_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            error_label.setStyleSheet(Styles.ERROR_STYLE)
            error_label.setWordWrap(True)
            layout.addWidget(error_label)
            logger.error(f"Error in history_window: {error_msg}")

        layout.addWidget(return_button)

        central_widget.setLayout(layout)
        logger.info("Navigated to History Window")

    def update_theme(self, theme):
        """Apply the selected theme to the application."""
        try:
            is_default_theme: bool = (theme == GUI.DEFAULT_THEME)
            if theme == GUI.LIGHT_THEME:
                RegistryHandler.change_theme(RegistryHandler.LIGHT_THEME)
            elif theme == GUI.DARK_THEME:
                RegistryHandler.change_theme(RegistryHandler.DARK_THEME)
            elif theme == GUI.DEFAULT_THEME:
                theme = RegistryHandler.retrieve_theme()
            else:
                logger.error("Invalid theme value provided to update_theme")
                return

            if theme == RegistryHandler.LIGHT_THEME:
                self.setStyleSheet(Styles.LIGHT_THEME)
            elif theme == RegistryHandler.DARK_THEME:
                self.setStyleSheet(Styles.DARK_THEME)
            Styles.update_theme_styles()

            if not is_default_theme:
                logger.info(f"Theme updated to {'Light' if theme == RegistryHandler.LIGHT_THEME else 'Dark'}")
                self.change_theme_window()
        except Exception as e:
            logger.error(f"Failed to update theme: {e}")

    def toggle_password_visibility(self, password_input, button):
        """Toggle the visibility of the password input field."""
        try:
            if button.isChecked():
                password_input.setEchoMode(QLineEdit.EchoMode.Normal)
                button.setIcon(QIcon(Styles.EYE_OFF_ICON_PATH))
                logger.info("Password visibility toggled ON")
            else:
                password_input.setEchoMode(QLineEdit.EchoMode.Password)
                button.setIcon(QIcon(Styles.EYE_ICON_PATH))
                logger.info("Password visibility toggled OFF")
        except Exception as e:
            logger.error(f"Failed to toggle password visibility: {e}")

    def show_success_popup(self, message: str, on_close=None):
        """Display a popup message indicating success."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Success")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        if on_close:
            msg_box.buttonClicked.connect(lambda button: on_close())
        msg_box.exec()

    def show_error_popup(self, message: str, on_close=None):
        """Display a popup message indicating an error."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error")
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        if on_close:
            msg_box.buttonClicked.connect(on_close)
        msg_box.exec()

if __name__ == "__main__":
    pass
