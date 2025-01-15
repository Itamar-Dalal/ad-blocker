from enum import StrEnum


class Errors(StrEnum):
    SERVER_ERROR: str = "1"
    SUBMIT_CODE_BEFORE_GETTING_IT: str = "2"
    INVALID_PASSWORD: str = "3"
    INVALID_EMAIL: str = "4"
    INVALID_CODE: str = "5"
    UPDATE_PASSWORD_BEFORE_PASSING_VERIFICATION: str = "6"
    EMAIL_NOT_EXIST: str = "7"
    INVALID_REQUEST: str = "8"
    INVALID_USERNAME: str = "9"
    USERNAME_IN_USE: str = "10"
    EMAIL_IN_USE: str = "11"
    USERNAME_NOT_EXIST: str = "12"
    INCORRECT_PASSWORD: str = "13"
    REGISTER_BEFORE_PASSING_EMAIL_VERIFICATION: str = "14"
    CODE_EXPIRED: str = "15"
