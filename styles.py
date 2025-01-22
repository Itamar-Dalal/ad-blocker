class Styles:
    # Window and Layout Constants
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300
    HOME_WINDOW_WIDTH = 775
    HOME_WINDOW_HEIGHT = 500
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
        background-color: #1A1A2E; /* Dark blue-gray */
        color: #D1DCE5;           /* Light blue-gray for text */
    }
    QPushButton {
        background-color: #2E4A78; /* Medium blue */
        color: #EAF2FB;            /* Light blue-white for text */
        border: 1px solid #3D5A91; /* Slightly darker blue for border */
        border-radius: 5px;        /* Optional: rounded corners */
    }
    QPushButton:hover {
        background-color: #3D5A91; /* Lighter blue on hover */
    }
    QPushButton:pressed {
        background-color: #233B5E; /* Darker blue on press */
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
    LOGO_PATH = r"assets\images\logo.png"
    LIGHT_MODE_IMAGE_PATH = r"assets\images\light_mode.png"
    DARK_MODE_IMAGE_PATH = r"assets\images\dark_mode.png"

    # Logo Dimensions
    LOGO_WIDTH = 120
    LOGO_HEIGHT = 120

    # Font Styles
    TITLE_STYLE = """
        font-size: 24px;
        font-weight: bold;
        color: #2c3e50;
        padding: 10px;
    """
    LABEL_STYLE = """
        font-size: 16px;
        font-weight: bold;
        color: #2c3e50;
    """
    INPUT_LABEL_STYLE = """
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
    """
    INPUT_STYLE = """
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
    FOOTER_STYLE = """
        font-size: 14px;
        color: #95a5a6;
    """
    SUBTITLE_STYLE = """
        font-size: 18px;
        color: #7f8c8d;
        margin-bottom: 5px;
    """

    # Button Styles
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
    
    # Window Title
    WINDOW_TITLE = "DNS AdBlocker"
    WINDOW_BACKGROUND = "background-color: white;"
    
    # Home Window Button Styles
    BUTTON_WIDTH = 200
    BUTTON_HEIGHT = 55