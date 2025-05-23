__author__ = "Itamar Dalal"

from PyQt6.QtWidgets import QApplication
import gui
from socket import socket, AF_INET, SOCK_STREAM, SOCK_DGRAM, SO_BROADCAST, SOL_SOCKET
from typing import Callable
import re
from protocol import Protocol, ProtocolOpcodes, ErrorCodes
from settings import Settings
import sys
import ctypes
import logging
import os
import ssl
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from ctypes import wintypes
from dns_config import DNSConfig
from datetime import datetime
from network import UDPHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Client:
    TIMEOUT: int = 5

    def __init__(self) -> None:
        """Initialize the Client class."""
        self.app = QApplication([])
        self.app.setWindowIcon(gui.GUI.get_app_icon())
        if sys.platform == "win32":
            myappid = "dnsadblocker.client.v1"
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
        self.window = None
        self.server = None
        self.protocol = Protocol()
        self.logged_in = False
        self.session_key = None  # AES session key
        self.udp_handler = UDPHandler()

    def __repr__(self) -> str:
        return f"Client()"
    
    @classmethod
    def create_client(cls) -> "Client":
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
            if "|" in username or "|" in password:
                self.window.login_window("Username and password cannot contain the '|' character.")
                return
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
            if "|" in domain:
                self.window.block_domain_window("Domain cannot contain the '|' character.")
                return
            # Validate domain
            if not Settings.MIN_DOMAIN_LENGTH.value <= len(domain) <= Settings.MAX_DOMAIN_LENGTH.value:
                self.window.block_domain_window(f"Domain Should be between {Settings.MIN_DOMAIN_LENGTH.value} and {Settings.MAX_DOMAIN_LENGTH.value} characters")
                return
            domain_regex = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
            if not re.match(domain_regex, domain):
                self.window.block_domain_window(f"Invalid domain: '{domain}'")
                return

            return call(self, domain)

        return func

    def verify_unblock_domain_args(call: Callable):
        def func(self, domain: str):
            if "|" in domain:
                self.window.unblock_domain_window("Domain cannot contain the '|' character.")
                return
            # Validate domain
            if not Settings.MIN_DOMAIN_LENGTH.value <= len(domain) <= Settings.MAX_DOMAIN_LENGTH.value:
                self.window.unblock_domain_window(f"Domain Should be between {Settings.MIN_DOMAIN_LENGTH.value} and {Settings.MAX_DOMAIN_LENGTH.value} characters")
                return
            
            domain_regex = r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})+$"
            if not re.match(domain_regex, domain):
                self.window.unblock_domain_window(f"Invalid domain: '{domain}'")
                return

            return call(self, domain)

        return func

    def verify_create_account_args(call: Callable):
        def func(self, username: str, password: str, email: str):
            if "|" in username or "|" in password or "|" in email:
                self.window.create_account_window("Username, password, and email cannot contain the '|' character.")
                return
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

    def verify_verification_args(call: Callable):
        def func(self, code: str):
            if "|" in code:
                self.window.email_verification_window("Verification code cannot contain the '|' character.")
                return
            if len(code) != 6:
                self.window.email_verification_window(
                    f'Invalid verification code: "{code}". Verification code must be 6 numbers.'
                )
                return
            return call(self, code)

        return func
    
    def verify_forgot_password_args(call: Callable):
        def func(self, email: str):
            if "|" in email:
                self.window.forgot_password_window("Email cannot contain the '|' character.")
                return
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                self.window.forgot_password_window(
                    f'Invalid email: "{email}". Email must be in format [???@???.???].'
                )
                return
            return call(self, email)

        return func
    
    def verify_reset_password_args(call: Callable):
        def func(self, password: str):
            if "|" in password:
                self.window.reset_password_window("Password cannot contain the '|' character.")
                return
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
    
    def verify_connect_to_dns_args(call: Callable):
        def func(self, interface: str, dns_ip: str):
            if interface == "":
                self.window.connect_to_dns_window(f"Interface name cannot be empty.")
                return
            # Regex to validate IPv4 addresses
            ip_regex = (
                r"^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\."
                r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$"
            )
            if not re.match(ip_regex, dns_ip):
                self.window.connect_to_dns_window(
                    f"Invalid DNS IP: {dns_ip}. IP must be in the format [0-255].[0-255].[0-255].[0-255]."
                )
                return

            return call(self, interface, dns_ip)
        return func

    @verify_connection_args
    def connect_to_server(self, ip: str, port: str) -> None:
        try:
            self.server = socket(AF_INET, SOCK_STREAM)
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            self.server = context.wrap_socket(self.server, server_hostname=ip)
            self.server.settimeout(Client.TIMEOUT)
            self.server.connect((ip, int(port)))
            logger.info(f"Connected to server at {ip}:{port} with TLS")
            # --- AES session key exchange with RSA encryption ---
            self.session_key = get_random_bytes(32)  # AES-256
            # Load server's public key from file (must match server.key)
            with open("server.key", "rb") as f:
                key_data = f.read()
                # Extract public key from private key file
                priv_key = RSA.import_key(key_data)
                pub_key = priv_key.publickey()
            cipher_rsa = PKCS1_OAEP.new(pub_key)
            encrypted_session_key = cipher_rsa.encrypt(self.session_key)
            # Send the length of the encrypted key first (4 bytes, big endian)
            self.server.sendall(len(encrypted_session_key).to_bytes(4, "big"))
            self.server.sendall(encrypted_session_key)
            logger.info("AES session key encrypted and sent to server")
            self.protocol.tcp_handler.session_key = self.session_key
            self.protocol.set_session_key(self.session_key)
        except (ConnectionRefusedError, TimeoutError, OSError) as e:
            logger.error(f"Cannot connect to server at {ip}:{port}: {e}")
            self.window.connect_to_server_window(
                f"Cannot find the server. Please enter a different IP or port."
            )
            return
        self.window.home_window()
    
    @verify_connect_to_dns_args
    def connect_to_dns(self, interface: str, dns_ip: str) -> None:
        DNSConfig.change_dns(interface, dns_ip)
        self.window.home_window()

    @verify_login_args
    def login(self, username: str, password: str) -> None:
        try:
            self.protocol.send_login(self.server, username, password)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                    self.logged_in = True
                    self.window.change_logged_in_status(self.logged_in)
                    self.window.show_success_popup("Login successful!", self.window.home_window)
                    return

                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_USERNAME.value:
                            self.window.login_window("Invalid username length.")
                        case ErrorCodes.INVALID_PASSWORD.value:
                            self.window.login_window("Invalid password. Must be 5-20 characters and contain at least one number.")
                        case ErrorCodes.INVALID_CREDENTIALS.value:
                            self.window.login_window("Invalid username or password.")
                        case ErrorCodes.TOO_MANY_ATTEMPTS.value:
                            self.window.login_window("Too many failed attempts. Please try again later.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.login_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in login: {e}")
            self.window.login_window(f"Error: {e}")

    def logout(self) -> None:
        try:
            self.protocol.send_logout(self.server)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                    self.logged_in = False
                    self.window.change_logged_in_status(self.logged_in)
                    self.window.show_success_popup("Logout successful!", self.window.home_window)
                    return

                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.NOT_LOGGED_IN.value:
                            self.window.show_error_popup("You are not logged in.", self.window.home_window)
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.show_error_popup("Server error occurred during logout.", self.window.home_window)
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in logout: {e}")
            self.window.show_error_popup(f"Error: {e}", self.window.home_window)

    @verify_block_domain_args
    def block_domain(self, domain: str) -> None:
        try:
            self.protocol.send_add_domain(self.server, domain)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                    logger.info(f"Domain '{domain}' successfully added")
                    self.window.show_success_popup(f"Domain '{domain}' successfully blocked!", self.window.home_window)
                    return
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.DOMAIN_IN_USE.value:
                            self.window.block_domain_window(f"Domain '{domain}' already blocked.")
                        case ErrorCodes.NOT_LOGGED_IN.value:
                            self.window.block_domain_window("You must be logged in to add a domain.")
                        case ErrorCodes.INVALID_DOMAIN.value:
                            self.window.block_domain_window("Invalid domain.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.block_domain_window("Server error.")
                        case _:
                            self.invalid_response(response)
                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in block_domain: {e}")
            self.window.block_domain_window(f"Error: {e}")

    @verify_unblock_domain_args
    def unblock_domain(self, domain: str) -> None:
        try:
            self.protocol.send_remove_domain(self.server, domain)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                    logger.info(f"Domain '{domain}' successfully removed")
                    self.window.show_success_popup(f"Domain '{domain}' successfully unblocked!", self.window.home_window)
                    return
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.DOMAIN_NOT_EXIST.value:
                            self.window.unblock_domain_window(f"Domain '{domain}' does not exist.")
                        case ErrorCodes.NOT_LOGGED_IN.value:
                            self.window.unblock_domain_window("You must be logged in to remove a domain.")
                        case ErrorCodes.INVALID_DOMAIN.value:
                            self.window.unblock_domain_window("Invalid domain format.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.unblock_domain_window("Server error.")
                        case _:
                            self.invalid_response(response)
                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in unblock_domain: {e}")
            self.window.unblock_domain_window(f"Error: {e}")

    @verify_create_account_args
    def create_account(self, username: str, password: str, email: str) -> None:
        try:
            self.protocol.send_create_user(self.server, username, password, email)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.EMAIL_VERIFICATION_CODE_SENT.value:
                    self.window.show_success_popup("Please verify your email.", self.window.email_verification_window)
                    return

                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_USERNAME.value:
                            self.window.create_account_window("Invalid username. Must be 3-20 characters.")
                        case ErrorCodes.INVALID_PASSWORD.value:
                            self.window.create_account_window("Invalid password. Must be 5-20 characters and contain at least one number.")
                        case ErrorCodes.INVALID_EMAIL.value:
                            self.window.create_account_window("Invalid email format.")
                        case ErrorCodes.USERNAME_IN_USE.value:
                            self.window.create_account_window("Username already in use.")
                        case ErrorCodes.EMAIL_IN_USE.value:
                            self.window.create_account_window("Email already in use.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.create_account_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in create_account: {e}")
            self.window.create_account_window(f"Error: {e}")

    @verify_verification_args
    def verify_email(self, code: str) -> None:
        try:
            self.protocol.send_verification_code(self.server, code)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.VERIFICATION_CODE_CORRECT.value:
                    self.window.show_success_popup("Email verified successfully!", self.window.home_window)
                    return
                
                case ProtocolOpcodes.VERIFICATION_CODE_INCORRECT.value:
                    self.window.email_verification_window(
                        f'Verification code: "{code}" is incorrect. Please try again.'
                    )
                    return

                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_CODE.value:
                            self.window.email_verification_window("Invalid code format.")
                        case ErrorCodes.CODE_EXPIRED.value:
                            self.window.email_verification_window("Verification code expired. Please request a new one.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.email_verification_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in verify_email: {e}")
            self.window.email_verification_window(f"Error: {e}")

    @verify_forgot_password_args
    def forgot_password(self, email: str) -> None:
        try:
            self.protocol.send_forgot_password(self.server, email)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.FORGOT_PASSWORD_CODE_SENT.value:
                    self.window.show_success_popup("Verification code sent to your email.", self.window.forgot_password_code_window)
                    return
                
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_EMAIL.value:
                            self.window.forgot_password_window("Invalid email format.")
                        case ErrorCodes.EMAIL_NOT_EXIST.value:
                            self.window.forgot_password_window("Email does not exist.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.forgot_password_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in forgot_password: {e}")
            self.window.forgot_password_window(f"Error: {e}")
    
    @verify_verification_args
    def forgot_password_code(self, code: str) -> None:
        try:
            self.protocol.send_forgot_password_code(self.server, code)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.FORGOT_PASSWORD_CODE_CORRECT.value:
                    self.window.show_success_popup("Verification code correct. Please enter a new password.", self.window.reset_password_window)
                    return
                
                case ProtocolOpcodes.FORGOT_PASSWORD_CODE_INCORRECT.value:
                    self.window.forgot_password_code_window(
                        f'Invalid verification code: "{code}". Please try again.'
                    )
                    return
                            
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_CODE.value:
                            self.window.forgot_password_code_window("Invalid code format.")
                        case ErrorCodes.CODE_EXPIRED.value:
                            self.window.forgot_password_code_window("Verification code expired. Please request a new one.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.forgot_password_code_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in forgot_password_code: {e}")
            self.window.forgot_password_code_window(f"Error: {e}")
    
    @verify_reset_password_args
    def reset_password(self, password: str) -> None:
        try:
            self.protocol.send_reset_password(self.server, password)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.ACKNOWLEDGMENT.value:
                    self.window.show_success_popup("Password reset successfully!", self.window.login_window)
                    return
                
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.INVALID_PASSWORD.value:
                            self.window.reset_password_window("Invalid password. Must be 5-20 characters and contain at least one number.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.reset_password_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in reset_password: {e}")
            self.window.reset_password_window(f"Error: {e}")

    def get_blocked_domains(self):
        try:
            self.protocol.send_get_blocked_domains(self.server)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            match opcode:
                case ProtocolOpcodes.BLOCKED_DOMAINS_RESPONSE.value:
                    blocked_domains = [
                        tuple(domain_data.split(","))
                        for domain_data in response[1:] if domain_data
                    ]
                    return blocked_domains
                
                case ProtocolOpcodes.ERROR.value:
                    error_code = self.handle_error(response)
                    match error_code:
                        case ErrorCodes.NOT_LOGGED_IN.value:
                            self.window.history_window("You must be logged in to view blocked domains.")
                        case ErrorCodes.SERVER_ERROR.value:
                            self.window.history_window("Server error.")
                        case _:
                            self.invalid_response(response)

                case _:
                    self.invalid_response(response)

        except Exception as e:
            logger.error(f"Exception in get_blocked_domains: {e}")
            self.window.history_window(f"Error: {e}")
            return []

    def get_all_users(self):
        try:
            self.protocol.send_get_all_users(self.server)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            if opcode == ProtocolOpcodes.ALL_USERS_RESPONSE.value:
                # Each user: username,email,password,salt
                users = [tuple(user.split(",")) for user in response[1:] if user]
                return users
            elif opcode == ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    case ErrorCodes.NOT_ADMIN.value:
                        self.window.admin_panel_window("You must be admin to view users.")
                    case ErrorCodes.SERVER_ERROR.value:
                        self.window.admin_panel_window("Server error.")
                    case _:
                        logger.error("Failed to get all users from server")
                return []
            else:
                self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in get_all_users: {e}")
            self.window.admin_panel_window(f"Error: {e}")
            return []

    def get_all_domains(self):
        try:
            self.protocol.send_get_all_domains(self.server)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            if opcode == ProtocolOpcodes.ALL_DOMAINS_RESPONSE.value:
                # Each domain: domain,username,time,source,is_blocked
                return [
                    (
                        d, u,
                        datetime.fromtimestamp(float(t)).strftime('%Y-%m-%d %H:%M:%S'),
                        s, b
                    )
                    for entry in response[1:] if entry
                    for d, u, t, s, b in [entry.split(",")]
                ]
            elif opcode == ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    case ErrorCodes.NOT_ADMIN.value:
                        self.window.admin_panel_window("You must be admin to view domains.")
                    case ErrorCodes.SERVER_ERROR.value:
                        self.window.admin_panel_window("Server error.")
                    case _:
                        logger.error("Failed to get all domains from server")
                return []
            else:
                self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in get_all_domains: {e}")
            self.window.admin_panel_window(f"Error: {e}")
            return []

    def delete_user(self, username):
        try:
            self.protocol.send_delete_user(self.server, username)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            if opcode == ProtocolOpcodes.ACKNOWLEDGMENT.value:
                logger.info(f"User '{username}' deleted successfully")
                return True
            elif opcode == ProtocolOpcodes.ERROR.value:
                error_code = self.handle_error(response)
                match error_code:
                    case ErrorCodes.NOT_ADMIN.value:
                        self.window.show_users_table()
                        logger.error("You must be admin to delete users.")
                    case ErrorCodes.CANNOT_DELETE_ADMIN.value:
                        self.window.show_users_table()
                        logger.error("Cannot delete admin user.")
                    case ErrorCodes.SERVER_ERROR.value:
                        self.window.show_users_table()
                        logger.error("Server error.")
                    case _:
                        logger.error(f"Failed to delete user '{username}'")
                return False
            else:
                self.invalid_response(response)
        except Exception as e:
            logger.error(f"Exception in delete_user: {e}")
            self.window.show_users_table()
            return False

    def get_current_username(self):
        try:
            self.protocol.send_get_current_username(self.server)
            response = self.protocol.recv_data(self.server)
            opcode = response[0]
            if opcode == ProtocolOpcodes.CURRENT_USERNAME_RESPONSE.value:
                return response[1] if len(response) > 1 else "guest"
            else:
                return "guest"
        except Exception as e:
            logger.error(f"Exception in get_current_username: {e}")
            return "guest"

    def handle_error(self, response: list) -> int:
        logger.error(f"Received Error: {' '.join(response)}")
        if len(response) < 2 or not response[1].isnumeric():
            self.invalid_response(response)
        error_code = response[1]
        return error_code

    def invalid_response(self, response: list) -> None:
        logger.error(f"Invalid response: {' '.join(response)}")
        self.exit_client()

    def exit_client(self) -> None:
        self.app.exit()
        if self.server:
            self.server.close()

    def run(self):
        """Check for admin privileges and run the client."""
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            is_admin = False

        if not is_admin:
            # show a Windows message box asking for admin permission
            response = ctypes.windll.user32.MessageBoxW(
                0,
                "This application requires administrative privileges to modify DNS settings.\nWould you like to run it as Administrator?",
                "Admin Privileges Required",
                0x00000004 | 0x00000030  # MB_YESNO | MB_ICONWARNING
            )

            if response == 6:  # IDYES
                # Relaunch the script with admin privileges using ShellExecuteEx
                script_path = os.path.abspath(sys.argv[0])
                params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
                try:
                    # Define SHELLEXECUTEINFO structure
                    class SHELLEXECUTEINFO(ctypes.Structure):
                        _fields_ = [
                            ("cbSize", wintypes.DWORD),
                            ("fMask", wintypes.ULONG),
                            ("hwnd", wintypes.HWND),
                            ("lpVerb", wintypes.LPCWSTR),
                            ("lpFile", wintypes.LPCWSTR),
                            ("lpParameters", wintypes.LPCWSTR),
                            ("lpDirectory", wintypes.LPCWSTR),
                            ("nShow", ctypes.c_int),
                            ("hInstApp", wintypes.HINSTANCE),
                            ("lpIDList", wintypes.LPVOID),
                            ("lpClass", wintypes.LPCWSTR),
                            ("hkeyClass", wintypes.HKEY),
                            ("dwHotKey", wintypes.DWORD),
                            ("hIcon", wintypes.HANDLE),
                            ("hProcess", wintypes.HANDLE),
                        ]

                    sei = SHELLEXECUTEINFO()
                    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
                    sei.fMask = 0x00000040  # SEE_MASK_NOCLOSEPROCESS
                    sei.hwnd = None
                    sei.lpVerb = "runas"  # Request elevation
                    sei.lpFile = sys.executable
                    sei.lpParameters = f'"{script_path}" {params}'.strip()
                    sei.lpDirectory = None
                    sei.nShow = 1  # SW_SHOWNORMAL
                    sei.hInstApp = None
                    sei.lpIDList = None
                    sei.lpClass = None
                    sei.hkeyClass = None
                    sei.dwHotKey = 0
                    sei.hIcon = None
                    sei.hProcess = None

                    success = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
                    if not success or sei.hInstApp < 32:
                        logger.error("Failed to elevate privileges via ShellExecuteEx")
                        ctypes.windll.user32.MessageBoxW(
                            0,
                            "Failed to run as Administrator. Please try again or run the application manually with admin rights.",
                            "Elevation Failed",
                            0x00000010  # MB_ICONERROR
                        )
                        sys.exit(1)
                    # Wait for the elevated process to start (optional, can be removed if not needed)
                    ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, 0xFFFFFFFF)  # INFINITE
                    ctypes.windll.kernel32.CloseHandle(sei.hProcess)
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"Failed to elevate privileges: {e}")
                    ctypes.windll.user32.MessageBoxW(
                        0,
                        "Failed to run as Administrator. Please try again or run the application manually with admin rights.",
                        "Elevation Failed",
                        0x00000010  # MB_ICONERROR
                    )
                    sys.exit(1)
            else:
                # User chose not to elevate, exit
                ctypes.windll.user32.MessageBoxW(
                    0,
                    "Administrative privileges are required to run this application. Exiting.",
                    "Permission Denied",
                    0x00000010  # MB_ICONERROR
                )
                sys.exit(1)
        else:
            # Already running as admin, proceed with client initialization
            self.window = gui.GUI(self)
            self.window.show()
            self.app.exec()

    def find_server_in_lan(self):
        """Broadcasts a UDP message to find the server in the LAN and connects if found."""
        try:
            udp_sock = socket(AF_INET, SOCK_DGRAM)
            udp_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            udp_sock.settimeout(3)
            self.udp_handler.send_to(udp_sock, Settings.BROADCAST_MESSAGE.value, ('<broadcast>', Settings.BROADCAST_PORT.value))
            logger.info("Broadcasted server discovery message on LAN")
            while True:
                data, addr = self.udp_handler.recv_from(udp_sock)
                if data is None:
                    break
                if data.startswith(Settings.BROADCAST_RESPONSE.value):
                    parts = data.decode().split(":")
                    server_ip = addr[0]
                    server_port = parts[1] if len(parts) > 1 else str(Settings.SERVER_PORT.value)
                    logger.info(f"Found server at {server_ip}:{server_port}")
                    self.connect_to_server(server_ip, server_port)
                    return
            self.window.connect_to_server_window("No server found in LAN.")
        except Exception as e:
            logger.error(f"Exception in find_server_in_lan: {e}")
            self.window.connect_to_server_window(f"Error: {e}")

    def find_dns_in_lan(self, interface: str):
        """Broadcasts a UDP message to find a DNS server in the LAN and fills the DNS IP field if found."""
        try:
            udp_sock = socket(AF_INET, SOCK_DGRAM)
            udp_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            udp_sock.settimeout(3)
            message = Settings.DNS_BROADCAST_MESSAGE.value + f"|{interface}".encode()
            self.udp_handler.send_to(udp_sock, message, ('<broadcast>', Settings.DNS_BROADCAST_PORT.value))
            logger.info(f"Broadcasted DNS discovery message on LAN for interface: {interface}")
            while True:
                data, addr = self.udp_handler.recv_from(udp_sock)
                if data is None:
                    break
                if data.startswith(Settings.DNS_BROADCAST_RESPONSE.value):
                    parts = data.decode().split(":")
                    dns_ip = parts[1]
                    logger.info(f"Found DNS server at {dns_ip}")
                    # Update the DNS IP input field in the GUI
                    self.window.update_dns_ip_field(dns_ip)
                    return
            self.window.connect_to_dns_window("No DNS server found in LAN.")
        except Exception as e:
            logger.error(f"Exception in find_dns_in_lan: {e}")
            self.window.connect_to_dns_window(f"Error: {e}")


if __name__ == "__main__":
    c = Client.create_client()
    c.run()
