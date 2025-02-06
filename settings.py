from enum import Enum

class Settings(Enum):
    MIN_USERNAME_LENGTH: int = 3
    MAX_USERNAME_LENGTH: int = 20

    MIN_PASSWORD_LENGTH: int = 5
    MAX_PASSWORD_LENGTH: int = 20
