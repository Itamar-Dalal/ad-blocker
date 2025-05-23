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
    GET_ALL_USERS: str = "GAUS"
    ALL_USERS_RESPONSE: str = "AUSR"
    GET_ALL_DOMAINS: str = "GADM"
    ALL_DOMAINS_RESPONSE: str = "ADMR"
    DELETE_USER: str = "DUSR"

    EMAIL_VERIFICATION_CODE_SENT: str = "EVCS"
    VERIFICATION_CODE_CORRECT: str = "CDEK"
    VERIFICATION_CODE_INCORRECT: str = "CDEW"
    FORGOT_PASSWORD_CODE_SENT: str = "FPCS"
    FORGOT_PASSWORD_CODE_CORRECT: str = "FPCO"
    FORGOT_PASSWORD_CODE_INCORRECT: str = "FPCW"
    BLOCKED_DOMAINS_RESPONSE: str = "BDRS"

    GET_CURRENT_USERNAME: str = "GCUN"
    CURRENT_USERNAME_RESPONSE: str = "CUSR"

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
    NOT_ADMIN: str = "20"
    CANNOT_DELETE_ADMIN: str = "21"
    TOO_MANY_ATTEMPTS: str = "22"

class Protocol:
    def __init__(self):
        """Initialize the Protocol with a TCPHandler for messaging."""
        self.tcp_handler = TCPHandler(True)
        self.session_key = None

    def set_session_key(self, key: bytes):
        """Set the session key for encryption and assign it to the TCPHandler."""
        self.session_key = key
        self.tcp_handler.session_key = key

    def send_create_user(self, sock: socket, username: str, password: str, email: str) -> None:
        """Send a create user request over the socket."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.CREATE_USER.value}|{username}|{password}|{email}", key=self.session_key)

    def send_login(self, sock: socket, username: str, password: str) -> None:
        """Send a login request."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.LOGIN.value}|{username}|{password}", key=self.session_key)

    def send_logout(self, sock: socket) -> None:
        """Send a logout request."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.LOGOUT.value}", key=self.session_key)

    def send_verification_code(self, sock: socket, code: str) -> None:
        """Send a verification code for email validation."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.VERIFICATION_CODE.value}|{code}", key=self.session_key)

    def send_forgot_password(self, sock: socket, email: str) -> None:
        """Initiate a forgot password procedure by sending the email."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD.value}|{email}", key=self.session_key)

    def send_forgot_password_code(self, sock: socket, code: str) -> None:
        """Send the code provided for resetting the password."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE.value}|{code}", key=self.session_key)

    def send_reset_password(self, sock: socket, new_password: str) -> None:
        """Send a request to reset the password to a new one."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.RESET_PASSWORD.value}|{new_password}", key=self.session_key)

    def send_add_domain(self, sock: socket, domain: str) -> None:
        """Send a request to add a domain to the block list."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ADD_DOMAIN.value}|{domain}", key=self.session_key)

    def send_remove_domain(self, sock: socket, domain: str) -> None:
        """Send a request to remove a domain from the block list."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.REMOVE_DOMAIN.value}|{domain}", key=self.session_key)

    def send_get_blocked_domains(self, sock: socket) -> None:
        """Request the list of currently blocked domains."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.GET_BLOCKED_DOMAINS.value}", key=self.session_key)

    def send_acknowledgment(self, sock: socket) -> None:
        """Send an acknowledgment message."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ACKNOWLEDGMENT.value}", key=self.session_key)

    def send_email_code_sent(self, sock: socket) -> None:
        """Notify that the email verification code has been sent."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.EMAIL_VERIFICATION_CODE_SENT.value}", key=self.session_key)

    def send_verification_code_status(self, sock: socket, is_code_correct: bool) -> None:
        """Send the status of the verification code check."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.VERIFICATION_CODE_CORRECT.value}" if is_code_correct else f"{ProtocolOpcodes.VERIFICATION_CODE_INCORRECT.value}", key=self.session_key)

    def send_forgot_password_code_sent(self, sock: socket) -> None:
        """Notify that the forgot password code has been sent."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE_SENT.value}", key=self.session_key)
    
    def send_forgot_password_code_status(self, sock: socket, is_code_correct: bool) -> None:
        """Send the status of the forgot password code validation."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE_CORRECT.value if is_code_correct else ProtocolOpcodes.FORGOT_PASSWORD_CODE_INCORRECT.value}", key=self.session_key)

    def send_blocked_domains_response(self, sock: socket, blocked_domains: list, key=None) -> None:
        """Send the list of blocked domains back to the client."""
        domains_str = "|".join(blocked_domains)
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.BLOCKED_DOMAINS_RESPONSE.value}|{domains_str}", key=self.session_key)
    
    def send_get_all_users(self, sock: socket) -> None:
        """Request the full list of users."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.GET_ALL_USERS.value}", key=self.session_key)

    def send_get_all_domains(self, sock: socket) -> None:
        """Request the full list of domains."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.GET_ALL_DOMAINS.value}", key=self.session_key)

    def send_delete_user(self, sock: socket, username: str) -> None:
        """Send a request to delete the specified user."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.DELETE_USER.value}|{username}", key=self.session_key)

    def send_get_current_username(self, sock: socket) -> None:
        """Request the current username from the server."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.GET_CURRENT_USERNAME.value}", key=self.session_key)

    def send_error(self, sock: socket, error_code: str) -> None:
        """Send an error message with the specified error code."""
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ERROR.value}|{error_code}", key=self.session_key)

    def recv_data(self, sock: socket) -> list:
        """Receive and parse incoming data from the socket."""
        response = self.tcp_handler.recv_by_size(sock, key=self.session_key)
        response = response.split("|")
        if len(response) == 0:
            logger.error("Error in recv_data: invalid response")
            raise ValueError("Invalid response")
        return response