__author__ = "Itamar Dalal"

import logging
from enum import StrEnum
from network import TCPHandler
from socket import socket

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProtocolOpcodes(StrEnum):
    ACKNOWLEDGMENT: str = "ACKG"
    CREATE_USER: str = "CUSR"
    LOGIN: str = "LOGN"
    LOGOUT: str = "LOUT"
    VERIFICATION_CODE: str = "VERC"
    FORGOT_PASSWORD: str = "FPWD"
    FORGOT_PASSWORD_CODE: str = "FPCD"
    RESET_PASSWORD: str = "RSPW"
    ADD_DOMAIN: str = "ADDM"
    REMOVE_DOMAIN: str = "REMD"
    GET_BLOCKED_DOMAINS: str = "GBDM"

    EMAIL_VERIFICATION_CODE_SENT: str = "EVCS"
    VERIFICATION_CODE_CORRECT: str = "CDEK"
    VERIFICATION_CODE_INCORRECT: str = "CDEW"
    FORGOT_PASSWORD_CODE_SENT: str = "FPCS"
    FORGOT_PASSWORD_CODE_CORRECT: str = "FPCO"
    FORGOT_PASSWORD_CODE_INCORRECT: str = "FPCW"
    BLOCKED_DOMAINS_RESPONSE: str = "BDRS"

    ERROR: str = "ERRO"

class ErrorCodes(StrEnum):
    SERVER_ERROR: str = "1"
    SUBMIT_CODE_BEFORE_GETTING_IT: str = "2"
    INVALID_PASSWORD: str = "3"
    INVALID_EMAIL: str = "4"
    INVALID_CODE: str = "5"
    EMAIL_NOT_EXIST: str = "6"
    INVALID_REQUEST: str = "7"
    INVALID_USERNAME: str = "8"
    USERNAME_IN_USE: str = "9"
    EMAIL_IN_USE: str = "10"
    USERNAME_NOT_EXIST: str = "11"
    INCORRECT_PASSWORD: str = "12"
    REGISTER_BEFORE_PASSING_EMAIL_VERIFICATION: str = "13"
    CODE_EXPIRED: str = "14"
    NOT_LOGGED_IN: str = "15"
    DOMAIN_IN_USE: str = "16"
    DOMAIN_NOT_EXIST: str = "17"
    INVALID_DOMAIN: str = "18"
    INVALID_CREDENTIALS: str = "19"

class Protocol:
    def __init__(self):
        self.tcp_handler = TCPHandler(True)

    def send_create_user(self, sock: socket, username: str, password: str, email: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.CREATE_USER.value}|{username}|{password}|{email}")

    def send_login(self, sock: socket, username: str, password: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.LOGIN.value}|{username}|{password}")

    def send_logout(self, sock: socket) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.LOGOUT.value}")

    def send_verification_code(self, sock: socket, code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.VERIFICATION_CODE.value}|{code}")

    def send_forgot_password(self, sock: socket, email: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD.value}|{email}")

    def send_forgot_password_code(self, sock: socket, code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE.value}|{code}")

    def send_reset_password(self, sock: socket, new_password: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.RESET_PASSWORD.value}|{new_password}")

    def send_add_domain(self, sock: socket, domain: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ADD_DOMAIN.value}|{domain}")

    def send_remove_domain(self, sock: socket, domain: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.REMOVE_DOMAIN.value}|{domain}")

    def send_get_blocked_domains(self, sock: socket) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.GET_BLOCKED_DOMAINS.value}")

    def send_acknowledgment(self, sock: socket) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ACKNOWLEDGMENT.value}")

    def send_email_code_sent(self, sock: socket) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.EMAIL_VERIFICATION_CODE_SENT.value}")

    def send_verification_code_status(self, sock: socket, is_code_correct: bool) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.VERIFICATION_CODE_CORRECT.value}" if is_code_correct else f"{ProtocolOpcodes.VERIFICATION_CODE_INCORRECT.value}")

    def send_forgot_password_code_sent(self, sock: socket) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE_SENT.value}")

    def send_forgot_password_code_status(self, sock: socket, is_code_correct: bool) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE_CORRECT.value}" if is_code_correct else f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE_INCORRECT.value}")

    def send_blocked_domains_response(self, sock: socket, blocked_domains: list) -> None:
        domains_str = "|".join(blocked_domains)
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.BLOCKED_DOMAINS_RESPONSE.value}|{domains_str}")

    def send_error(self, sock: socket, error_code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ERROR.value}|{error_code}")

    def recv_data(self, sock: socket) -> list:
        response = self.tcp_handler.recv_by_size(sock)
        response = response.split("|")
        if len(response) == 0:
            logger.error("Error in recv_data: invalid response")
            raise ValueError("Invalid response")
        return response