from registry import RegistryHandler

class Styles:
    # Window and Layout Constants
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300
    LAYOUT_SPACING = 20
    BUTTON_SPACING = 35
    BUTTON_MARGINS = (50, 0, 50, 0)

    LIGHT_THEME = """
    QWidget {
        background-color: white;
        color: black;
    }
    QPushButton {
        background-color: lightgray;
        color: black;
    }
    """

    DARK_THEME = """
    QWidget {
        background-color: #2c2f3e;
        color: #D1DCE5;
    }
    QPushButton {
        background-color: #2E4A78; 
        color: #EAF2FB;            
        border: 1px solid #3D5A91; 
        border-radius: 5px;        
    }
    QPushButton:hover {
        background-color: #3D5A91;
    }
    QPushButton:pressed {
        background-color: #233B5E;
    }
    """

    # Colors and Effects
    SHADOW_EFFECT_COLOR = (150, 150, 150, 150)
    SHADOW_COLOR = (100, 100, 100, 150)
    SHADOW_BLUR_RADIUS = 10
    SHADOW_OFFSET = (5, 5)
    BUTTON_HOVER_COLOR = "#2980b9"
    BUTTON_PRESSED_COLOR = "#1e6f98"
    BUTTON_BORDER_COLOR = "#2980b9"
    BUTTON_PRESSED_BORDER_COLOR = "#145374"

    # File Paths
    ICON_PATH = r"assets\icons\icon.png"
    EYE_ICON_PATH = r"assets\icons\eye_icon.png"
    EYE_OFF_ICON_PATH = r"assets\icons\eye_off_icon.png"
    LOGO_PATH = r"assets\images\logo.png"
    LOGO_WITH_BACKGROUND_PATH = r"assets\images\logo_with_background.png"
    LIGHT_MODE_IMAGE_PATH = r"assets\images\light_mode.png"
    DARK_MODE_IMAGE_PATH = r"assets\images\dark_mode.png"

    # Logo Dimensions
    LOGO_WIDTH = 120
    LOGO_HEIGHT = 120

    TOGGLE_BUTTON_STYLE = """
        QToolButton {
            background-color: white;
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 2px;
        }
        QToolButton:hover {
            background-color: #f0f0f0;
        }
        QToolButton:checked {
            background-color: #e0e0e0;
        }
    """

    ERROR_STYLE = """
        QLabel {
            color: red;
            font-size: 14px;
            font-weight: bold;
            white-space: normal;
        }
        QLineEdit {
            border: 2px solid red;
            background-color: #ffe6e6;
        }
    """

    BUTTON_STYLE = """
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
    WINDOW_TITLE = "DNS AdBlocker"
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 55

    @staticmethod
    def update_theme_styles():
        if RegistryHandler.retrieve_theme() == RegistryHandler.LIGHT_THEME:
            Styles.INPUT_STYLE = """
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
            Styles.TITLE_STYLE = """
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
            """
            Styles.LABEL_STYLE = """
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
            """
            Styles.INPUT_LABEL_STYLE = """
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
            """
            Styles.FOOTER_STYLE = """
                font-size: 14px;
                color: #95a5a6;
            """
            Styles.SUBTITLE_STYLE = """
                font-size: 18px;
                color: #7f8c8d;
                margin-bottom: 5px;
            """
        else:
            Styles.INPUT_STYLE = """
                QLineEdit {
                    font-size: 16px;
                    padding: 8px;
                    border: 2px solid #2980b9;
                    border-radius: 10px;
                    color: white;
                }
                QLineEdit:focus {
                    border: 2px solid #3498db;
                }
            """
            Styles.TITLE_STYLE = """
                font-size: 24px;
                font-weight: bold;
                color: #e8e8e8;
                padding: 10px;
            """
            Styles.LABEL_STYLE = """
                font-size: 16px;
                font-weight: bold;
                color: #e8e8e8;
            """
            Styles.INPUT_LABEL_STYLE = """
                font-size: 18px;
                font-weight: bold;
                color: #e8e8e8;
            """
            Styles.FOOTER_STYLE = """
                font-size: 14px;
                color: #d1d1d1;
            """
            Styles.SUBTITLE_STYLE = """
                font-size: 18px;
                color: #c8c8c8;
                margin-bottom: 5px;
            """