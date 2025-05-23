__author__ = "Itamar Dalal"

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

    ADMIN_USERNAME: str = "system"

    CHUNK_SIZE = 1000
    LOADING_DELAY = 0.1

    SERVER_PORT: int = 1234
    
    BROADCAST_PORT = 54545
    BROADCAST_MESSAGE = b"ADBLOCKER_DISCOVERY"
    BROADCAST_RESPONSE = b"ADBLOCKER_SERVER_HERE"
    DNS_SERVER_IP: str = "127.0.0.1"

    DNS_BROADCAST_PORT = 54546
    DNS_BROADCAST_MESSAGE = b"DNS_ADBLOCKER_DISCOVERY"
    DNS_BROADCAST_RESPONSE = b"DNS_ADBLOCKER_HERE"