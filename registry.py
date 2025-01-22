from winreg import HKEY_CURRENT_USER, CreateKey, SetValueEx, REG_DWORD, KEY_ALL_ACCESS, OpenKey, QueryValueEx

class RegistryHandler:
    REGISTRY_PATH = r"Software\AdBlocker"
    SETTINGS_PATH = "settings"

    THEME_VALUE_NAME = "Theme"
    LIGHT_THEME = 0
    DARK_THEME = 1

    def __init__(self):
        try:
            self.key = HKEY_CURRENT_USER
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            CreateKey(self.key, settings_key_path)
            with OpenKey(self.key, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                try:
                    QueryValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME)
                except FileNotFoundError:
                    self.change_theme(RegistryHandler.LIGHT_THEME) # Default theme is light
        except Exception as e:
            print(f"Failed to initialize RegistryHandler: {e}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def change_theme(self, theme_value: int):
        try:
            if theme_value not in (RegistryHandler.LIGHT_THEME, RegistryHandler.DARK_THEME):
                raise ValueError(f"Invalid theme value: {theme_value}. Must be either {RegistryHandler.LIGHT_THEME} or {RegistryHandler.DARK_THEME}")
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            with OpenKey(self.key, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                SetValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME, 0, REG_DWORD, theme_value)
                #print(f"Theme changed to {'dark' if theme_value else 'light'} successfully")
        except Exception as e:
            print(f"Failed to change theme: {e}")

    def retrieve_theme(self) -> int:
        try:
            settings_key_path = rf"{RegistryHandler.REGISTRY_PATH}\{RegistryHandler.SETTINGS_PATH}"
            with OpenKey(self.key, settings_key_path, 0, KEY_ALL_ACCESS) as settings_key:
                theme_value, _ = QueryValueEx(settings_key, RegistryHandler.THEME_VALUE_NAME)
                return theme_value
        except Exception as e:
            print(f"Failed to retrieve theme: {e}")
            return -1

if __name__ == "__main__":
    with RegistryHandler() as registry_handler:
        registry_handler.retrieve_theme()