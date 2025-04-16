from enum import Enum

class Settings(Enum):
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 20

    MIN_PASSWORD_LENGTH: int = 5
    MAX_PASSWORD_LENGTH: int = 20

    MAX_DOMAIN_LENGTH: int = 255
    MIN_DOMAIN_LENGTH: int = 3

    EMAIL_CODE_LENGTH: int = 6
    SERVER_EMAIL: str = "dalalcyber@gmail.com"
    SERVER_EMAIL_PASSWORD: str = "bgzrldhsppxdjeko"
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    EMAIL_CODE_TIMEOUT: int = 300  # 5 minutes

    DATABASE_PATH = b"adblocker.db"