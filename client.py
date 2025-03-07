from PyQt6.QtWidgets import QApplication
import gui
from socket import socket, AF_INET, SOCK_STREAM
from typing import Callable
import re
from protocol import Protocol, ProtocolOpcodes, ErrorCodes
from settings import Settings


class Client:
    TIMEOUT: int = 5

    def __init__(self) -> None:
        """Initialize the Client class."""
        self.app = QApplication([])
        self.window = None
        self.server = None
        self.protocol = Protocol()

    def __repr__(self) -> str:
        """Return a string representation of the Client."""
        return f"Client()"

    @classmethod
    def create_client(cls) -> "Client":
        """Factory method to create and return a Client instance."""
        return cls()

    def verify_connection_args(call: Callable):
        def func(self, ip: str, port: str):
            if ip == "" or port == "":
                self.window.connect_to_server_window(f"IP and Port cannot be empty.")
                return

            # Regex to validate IPv4 addresses
            ip_regex = (
                r"^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$"
            )

            # Validate IP
            if not re.match(ip_regex, ip):
                self.window.connect_to_server_window(
                    f"Invalid IP: {ip}. IP must be in the format [0-255].[0-255].[0-255].[0-255]."
                )
                return

            # Validate port
            if not port.isnumeric() or not (1 <= int(port) <= 65535):
                self.window.connect_to_server_window(
                    f"Invalid port: {port}. Port must be a number between 1 and 65535."
                )
                return

            return call(self, ip, port)

        return func

    def verify_login_args(call: Callable):
        def func(self, username: str, password: str):
            # Validate username
            if (
                len(username) < Settings.MIN_USERNAME_LENGTH.value
                or len(username) > Settings.MAX_USERNAME_LENGTH.value
            ):
                self.window.login_window(
                    f'Invalid username: "{username}". Username must be between {Settings.MIN_USERNAME_LENGTH.value} and {Settings.MAX_USERNAME_LENGTH.value} characters.'
                )
                return

            # Validate password
            if (
                len(password) < Settings.MIN_PASSWORD_LENGTH.value
                or len(password) > Settings.MAX_PASSWORD_LENGTH.value
            ):
                self.window.login_window(
                    f'Invalid password: "{password}". Password must be between {Settings.MIN_PASSWORD_LENGTH.value} and {Settings.MAX_PASSWORD_LENGTH.value} characters.'
                )
                return

            if not re.search(r"\d", password):
                self.window.login_window(
                    f'Invalid password: "{password}". Password must contain at least one number.'
                )
                return

            #if not re.search(r"[A-Z]", password):
            #    self.window.login_window(
            #        f'Invalid password: "{password}". Password must contain at least one uppercase letter.'
            #    )
            #    return

            return call(self, username, password)

        return func

    def verify_block_domain_args(call: Callable):
        def func(self, domain: str):
            pass
            return call(self, domain)

        return func

    def verify_create_account_args(call: Callable):
        def func(self, username: str, password: str, email: str):
            # Validate username
            if (
                len(username) < Settings.MIN_USERNAME_LENGTH.value
                or len(username) > Settings.MAX_USERNAME_LENGTH.value
            ):
                self.window.create_account_window(
                    f'Invalid username: "{username}". Username must be between {Settings.MIN_USERNAME_LENGTH.value} and {Settings.MAX_USERNAME_LENGTH.value} characters.'
                )
                return

            # Validate password
            if (
                len(password) < Settings.MIN_PASSWORD_LENGTH.value
                or len(password) > Settings.MAX_PASSWORD_LENGTH.value
            ):
                self.window.create_account_window(
                    f'Invalid password: "{password}". Password must be between {Settings.MIN_PASSWORD_LENGTH.value} and {Settings.MAX_PASSWORD_LENGTH.value} characters.'
                )
                return

            if not re.search(r"\d", password):
                self.window.create_account_window(
                    f'Invalid password: "{password}". Password must contain at least one number.'
                )
                return

            #if not re.search(r"[A-Z]", password):
            #    self.window.create_account_window(
            #        f'Invalid password: "{password}". Password must contain at least one uppercase letter.'
            #    )
            #    return

            # Validate email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self.window.create_account_window(
                    f'Invalid email: "{email}". Email must be in format [???@???.???].'
                )
                return
            return call(self, username, password, email)

        return func

    def verify_verficication_args(call: Callable):
        def func(self, code: str):
            if len(code) != 6:
                self.window.email_verification_window(
                    f'Invalid verification code: "{code}". Verification code must be 6 numbers.'
                )
                return
            return call(self, code)

        return func
    
    def verify_forgot_password_args(call: Callable):
        def func(self, email: str):
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self.window.forgot_password_window(
                    f'Invalid email: "{email}". Email must be in format [???@???.???].'
                )
                return
            return call(self, email)

        return func
    
    def verify_reset_password_args(call: Callable):
        def func(self, password: str):
            if (
                len(password) < Settings.MIN_PASSWORD_LENGTH.value
                or len(password) > Settings.MAX_PASSWORD_LENGTH.value
            ):
                self.window.reset_password_window(
                    f'Invalid password: "{password}". Password must be between {Settings.MIN_PASSWORD_LENGTH.value} and {Settings.MAX_PASSWORD_LENGTH.value} characters.'
                )
                return

            if not re.search(r"\d", password):
                self.window.reset_password_window(
                    f'Invalid password: "{password}". Password must contain at least one number.'
                )
                return

            return call(self, password)

        return func

    @verify_connection_args
    def connect_to_server(self, ip: str, port: str) -> None:
        try:
            self.server = socket(AF_INET, SOCK_STREAM)
            self.server.settimeout(Client.TIMEOUT)
            self.server.connect((ip, int(port)))
            print(f"Connected to server at {ip}:{port}")
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            self.window.connect_to_server_window(
                f"Cannot find the server. Please enter a different IP or port."
            )
            return
        self.window.home_window()

    @verify_login_args
    def login(self, username: str, password: str) -> None:
        self.protocol.send_login(self.server, username, password)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                self.window.home_window()
                # TODO: add pop up window
                return

            case ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    # TODO: add error codes
                    case _:
                        self.invalid_response(response)

            case _:
                self.invalid_response(response)

    @verify_block_domain_args
    def block_domain(self, domain: str) -> None:
        pass

    @verify_create_account_args
    def create_account(self, username: str, password: str, email: str) -> None:
        self.protocol.send_create_user(self.server, username, password, email)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.EMAIL_VERIFICATION_CODE_SENT.value:
                self.window.email_verification_window()
                return

            case ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    # TODO: add error codes
                    case _:
                        self.invalid_response(response)

            case _:
                self.invalid_response(response)

    @verify_verficication_args
    def verify_email(self, code: str) -> None:
        self.protocol.send_verficication_code(self.server, code)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.VERIFICATION_CODE_CORRECT.value:
                self.window.home_window()
                # TODO: add pop up window
                return
            
            case ProtocolOpcodes.VERIFICATION_CODE_INCORRECT.value:
                self.window.email_verification_window(
                    f'Verification code: "{code}" is incorrect. Please try again.'
                )
                return

            case ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    # TODO: add error codes
                    case _:
                        self.invalid_response(response)

            case _:
                self.invalid_response(response)

    @verify_forgot_password_args
    def forgot_password(self, email: str) -> None:
        self.protocol.send_forgot_password(self.server, email)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.FORGOT_PASSWORD_CODE_SENT.value:
                self.window.forgot_password_code_window()
                return
            
            case ProtocolOpcodes.ERROR.value:
               error_code = self.handle_error(response)
               match error_code:
                   # TODO: add error codes
                   case _:
                       self.invalid_response(response)

            case _:
                self.invalid_response(response)
    
    @verify_verficication_args
    def forgot_password_code(self, code: str) -> None:
        self.protocol.send_forgot_password_code(self.server, code)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.FORGOT_PASSWORD_CODE_CORRECT.value:
                self.window.reset_password_window()
                return
            
            case ProtocolOpcodes.FORGOT_PASSWORD_CODE_INCORRECT.value:
                self.window.forgot_password_code_window(
                    f'Invalid verification code: "{code}". Please try again.'
                )
                return
                        
            case ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    # TODO: add error codes
                    case _:
                       self.invalid_response(response)

            case _:
                self.invalid_response(response)
    
    @verify_reset_password_args
    def reset_password(self, password: str) -> None:
        self.protocol.send_reset_password(self.server, password)
        response = self.protocol.recv_data(self.server)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                self.window.login_window()
                # TODO: add pop up window
                return
            
            case ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    # TODO: add error codes
                    case _:
                       self.invalid_response(response)

            case _:
                self.invalid_response(response)

    def handle_error(self, response: list) -> int:
        print(f'Received Error: {" ".join(response)}')

        if len(response) < 2 or response[1].isnumeric() is False:
            self.invalid_response()

        error_code = int(response[1])
        return error_code

    def invalid_response(self, response: list) -> None:
        print(f'Invalid response: {" ".join(response)}')
        self.exit_client()

    def exit_client(self) -> None:
        self.app.exit()
        self.server.close()

    def run(self):
        self.window = gui.GUI(self)
        self.window.show()
        self.app.exec()


if __name__ == "__main__":
    c = Client.create_client()
    c.run()
