from enum import StrEnum
from network import TCPHandler
from socket import socket

class ProtocolOpcodes(StrEnum):
    ACKNOWLEDGMENT: str = "ACKG"
    CREATE_USER: str = "CUSR"
    LOGIN: str = "LOGN"
    VERIFICATION_CODE: str = "VERC"
    FORGOT_PASSWORD: str = "FPWD"
    FORGOT_PASSWORD_CODE: str = "FPCD"
    RESET_PASSWORD: str = "RSPW"

    EMAIL_VERIFICATION_CODE_SENT: str = "EVCS"
    VERIFICATION_CODE_CORRECT: str = "CDEK"
    VERIFICATION_CODE_INCORRECT: str = "CDEW"
    FORGOT_PASSWORD_CODE_SENT: str = "FPCS" 
    FORGOT_PASSWORD_CODE_CORRECT: str = "FPCO"
    FORGOT_PASSWORD_CODE_INCORRECT: str = "FPCW"

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
    

class Protocol:
    def __init__(self):
        self.tcp_handler = TCPHandler(True)

    # Client methods
    def send_create_user(self, sock: socket, username: str, password: str, email: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.CREATE_USER.value}|{username}|{password}|{email}")
    
    def send_login(self, sock: socket, username: str, password: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.LOGIN.value}|{username}|{password}")
    
    def send_verification_code(self, sock: socket, code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.VERIFICATION_CODE.value}|{code}")

    def send_forgot_password(self, sock: socket, email: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD.value}|{email}")

    def send_forgot_password_code(self, sock: socket, code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.FORGOT_PASSWORD_CODE.value}|{code}")
    
    def send_reset_password(self, sock: socket, new_password: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.RESET_PASSWORD.value}|{new_password}")
                                                 
    # Server methods
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

    def send_error(self, sock: socket, error_code: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.ERROR.value}|{error_code}")

    def recv_data(self, sock: socket) -> list:
        response = self.tcp_handler.recv_by_size(sock)
        response = response.split("|")
        if len(response) == 0:
            print("Error in recv_data: invalid response")
            # TODO: send error
            raise ValueError("Invalid response")
        return response

if __name__ == "__main__":
    protocol = Protocol()
