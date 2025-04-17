import logging
from winreg import HKEY_CURRENT_USER, CreateKey, SetValueEx, REG_DWORD, KEY_ALL_ACCESS, OpenKey, QueryValueEx

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RegistryHandler:
    """
    A handler class for managing registry settings related to the AdBlocker application.
    Attributes:
        REGISTRY_PATH (str): The base path in the registry for AdBlocker settings.
        SETTINGS_PATH (str): The sub-path in the registry for settings.
        THEME_VALUE_NAME (str): The name of the registry value for the theme setting.
        LIGHT_THEME (int): The value representing the light theme.
        DARK_THEME (int): The value representing the dark theme.
        KEY: The registry key (HKEY_CURRENT_USER).
    Methods:
        __init__(): Initializes the RegistryHandler, creates the settings key if it doesn't exist, and sets the default theme.
        __enter__(): Enters the runtime context related to this object.
        __exit__(exc_type, exc_val, exc_tb): Exits the runtime context related to this object.
        change_theme(theme_value: int): Changes the theme setting in the registry.
        retrieve_theme() -> int: Retrieves the current theme setting from the registry.
    """
    
    REGISTRY_PATH = r"Software\AdBlocker"
    SETTINGS_PATH = "settings"

    THEME_VALUE_NAME = "Theme"
    LIGHT_THEME = 0
    DARK_THEME = 1

    KEY = HKEY_CURRENT_USER
    def __init__(self):
        try:
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            CreateKey(RegistryHandler.KEY, settings_key_path)
            with OpenKey(RegistryHandler.KEY, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                try:
                    QueryValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME)
                except FileNotFoundError:
                    self.change_theme(RegistryHandler.LIGHT_THEME) # Default theme is light
        except Exception as e:
            logger.error(f"Failed to initialize RegistryHandler: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    @staticmethod
    def change_theme(theme_value: int):
        try:
            if theme_value not in (RegistryHandler.LIGHT_THEME, RegistryHandler.DARK_THEME):
                raise ValueError(f"Invalid theme value: {theme_value}. Must be either {RegistryHandler.LIGHT_THEME} or {RegistryHandler.DARK_THEME}")
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            with OpenKey(RegistryHandler.KEY, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                SetValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME, 0, REG_DWORD, theme_value)
                logger.info(f"Theme changed to {'dark' if theme_value else 'light'} successfully")
        except Exception as e:
            logger.error(f"Failed to change theme: {e}")

    @staticmethod
    def retrieve_theme() -> int:
        try:
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            with OpenKey(RegistryHandler.KEY, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                theme_value, _ = QueryValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME)
                return theme_value
        except Exception as e:
            logger.error(f"Failed to retrieve theme: {e}")
            return -1

if __name__ == "__main__":
    with RegistryHandler() as registry_handler:
        registry_handler.retrieve_theme()