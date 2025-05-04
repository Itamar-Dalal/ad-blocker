__author__ = "Itamar Dalal"

from sys import argv
from threading import Thread, Semaphore
import socket
from socket import socket, AF_INET, SOCK_STREAM, error, gaierror, gethostbyname
import ssl
from protocol import Protocol, ProtocolOpcodes, ErrorCodes
from settings import Settings
import re
from random import randrange
import smtplib
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import UsersDBHandler, EmailCodeDBHandler, DomainsDBHandler
from styles import Styles
from time import time
import logging
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP

IP = "0.0.0.0"
PORT = 1234

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Server:
    MAX_CLIENTS = 1000
    BACKLOG = 5
    RATE_LIMIT_WINDOW = 60
    MAX_ATTEMPTS = 5

    def __init__(self, ip=IP, port=PORT) -> None:
        self.ip = ip
        self.port = port
        self.srv_sock = socket(AF_INET, SOCK_STREAM)
        self.threads = []
        self.semaphore = Semaphore(Server.MAX_CLIENTS)
        self.protocol = Protocol()
        self.db_handler = UsersDBHandler()
        self.email_code_db_handler = EmailCodeDBHandler()
        self.domains_db_handler = DomainsDBHandler()
        self.logged_in_users = {}
        self.login_attempts = {}

    def __repr__(self) -> str:
        return f"Server({self.ip}, {self.port})"

    def create_server(cls) -> "Server":
        return cls()

    def handle_client(self, cli_sock, addr):
        session_key = None
        try:
            # --- AES session key exchange with RSA decryption ---
            # Receive the length of the encrypted key (4 bytes, big endian)
            enc_key_len = int.from_bytes(cli_sock.recv(4), "big")
            encrypted_session_key = b""
            while len(encrypted_session_key) < enc_key_len:
                chunk = cli_sock.recv(enc_key_len - len(encrypted_session_key))
                if not chunk:
                    raise ConnectionError("Failed to receive encrypted session key")
                encrypted_session_key += chunk
            # Load server's private key from file
            with open("server.key", "rb") as f:
                priv_key = RSA.import_key(f.read())
            cipher_rsa = PKCS1_OAEP.new(priv_key)
            session_key = cipher_rsa.decrypt(encrypted_session_key)
            self.protocol.tcp_handler.session_key = session_key
            self.protocol.set_session_key(session_key)
            while True:
                request = self.protocol.recv_data(cli_sock)
                opcode = request[0]
                match opcode:
                    case ProtocolOpcodes.CREATE_USER.value:
                        self.handle_register(cli_sock, addr, request)
                    case ProtocolOpcodes.FORGOT_PASSWORD.value:
                        self.handle_forgot_password(cli_sock, addr, request)
                    case ProtocolOpcodes.LOGIN.value:
                        self.handle_login(cli_sock, addr, request)
                    case ProtocolOpcodes.LOGOUT.value:
                        self.handle_logout(cli_sock, addr)
                    case ProtocolOpcodes.ADD_DOMAIN.value:
                        self.handle_add_domain(cli_sock, addr, request)
                    case ProtocolOpcodes.REMOVE_DOMAIN.value:
                        self.handle_remove_domain(cli_sock, addr, request)
                    case ProtocolOpcodes.GET_BLOCKED_DOMAINS.value:
                        self.handle_get_blocked_domains(cli_sock)
                    case ProtocolOpcodes.GET_ALL_USERS.value:
                        self.handle_get_all_users(cli_sock)
                    case ProtocolOpcodes.GET_ALL_DOMAINS.value:
                        self.handle_get_all_domains(cli_sock)
                    case ProtocolOpcodes.DELETE_USER.value:
                        self.handle_delete_user(cli_sock, request)
                    case ProtocolOpcodes.GET_CURRENT_USERNAME.value:
                        self.handle_get_current_username(cli_sock)
                    case _:
                        self.invalid_request(cli_sock, addr, request)
                        return
        except Exception as e:
            logger.error(f"Thread for client at {addr} terminated: {e}")
        finally:
            self.close_client_connection(cli_sock, addr)

    def handle_register(self, cli_sock, addr, request: list) -> None:
        username, password, email = request[1:]
        if not Settings.MIN_USERNAME_LENGTH.value <= len(username) <= Settings.MAX_USERNAME_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_USERNAME.value)
            return
        if not Settings.MIN_PASSWORD_LENGTH.value <= len(password) <= Settings.MAX_PASSWORD_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
            return
        if not re.search(r"\d", password):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
            return

        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_EMAIL.value)
            return
        if self.db_handler.is_username_exist(username):
            self.protocol.send_error(cli_sock, ErrorCodes.USERNAME_IN_USE.value)
            return
        if self.db_handler.is_email_exist(email):
            self.protocol.send_error(cli_sock, ErrorCodes.EMAIL_IN_USE.value)
            return

        email_code = Server.send_verification_code(email, True)
        self.email_code_db_handler.save_email(email)
        self.protocol.send_email_code_sent(cli_sock)
        response = self.protocol.recv_data(cli_sock)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.VERIFICATION_CODE.value:
                client_code = response[1]
                if len(client_code) != 6 or not client_code.isnumeric():
                    self.protocol.send_error(cli_sock, ErrorCodes.INVALID_CODE.value)
                    return

                if self.email_code_db_handler.is_timeout_passed(email):
                    self.email_code_db_handler.delete_email(email)
                    self.protocol.send_error(cli_sock, ErrorCodes.CODE_EXPIRED.value)
                    return

                is_code_correct = (client_code == email_code)
                self.protocol.send_verification_code_status(cli_sock, is_code_correct)
                if not is_code_correct:
                    return

            case ProtocolOpcodes.CREATE_USER.value:
                self.handle_register(cli_sock, addr, response)
                return

            case _:
                self.invalid_request(cli_sock, addr, response)
                return

        self.db_handler.save_user(username, email, password)
        self.email_code_db_handler.delete_email(email)
        logger.info(f"User registered successfully: {username}, {email}")

    def send_verification_code(receiver_email: str, to_verify_email: bool) -> str:
        try:
            code_length = Settings.EMAIL_CODE_LENGTH.value
            code = f"{randrange(10 ** (code_length - 1), (10 ** code_length) - 1):0{code_length}d}"

            message = MIMEMultipart("alternative")
            message["From"] = Settings.SERVER_EMAIL.value
            message["To"] = receiver_email
            message["Subject"] = ("Email Verification Code - AdBlocker" if to_verify_email
                               else "Forgot Password Code - AdBlocker")

            html = f"""\
            <html>
            <body style="text-align: center;">
                <p style="font-size: 20px; margin: 20px 0;">
                    Your code for {'email verification' if to_verify_email else 'password reset'} is: <b>{code}</b>
                </p>
                <div style="margin: 20px auto; padding: 15px; background-color: #f0f0f0; border-radius: 5px; width: 200px; text-align: center;">
                    <p style="margin: 0; font-size: 16px;">This code expires in:</p>
                    <img src="https://i.countdownmail.com/41vs0z.gif?send_time={int(time())}" border="0" alt="countdownmail.com"/>
                </div>
                <img src="cid:logo" width="500" height="500" style="display: block; margin: 0 auto;">
                <br>
                <i style="display: block;">Developed by Itamar Dalal © 2024-2025</i>
            </body>
            </html>
            """
            message.attach(MIMEText(html, "html"))

            with open(Styles.LOGO_WITH_BACKGROUND_PATH, "rb") as img:
                mime_image = MIMEImage(img.read())
                mime_image.add_header("Content-ID", "<logo>")
                mime_image.add_header("Content-Disposition", "inline", filename="logo")
                message.attach(mime_image)

            with smtplib.SMTP(Settings.SMTP_SERVER.value, Settings.SMTP_PORT.value) as server:
                server.starttls()
                server.login(Settings.SERVER_EMAIL.value, Settings.SERVER_EMAIL_PASSWORD.value)
                server.sendmail(Settings.SERVER_EMAIL.value, receiver_email, message.as_string())

            logger.info(f"Email successfully sent from {Settings.SERVER_EMAIL.value} to {receiver_email}")
            return code

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email: {str(e)}")
            return None
        except FileNotFoundError as e:
            logger.error(f"Logo file not found: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return None

    def handle_forgot_password(self, cli_sock, addr, request: list) -> None:
        email = request[1]
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_EMAIL.value)
            return
        if not self.db_handler.is_email_exist(email):
            self.protocol.send_error(cli_sock, ErrorCodes.EMAIL_NOT_EXIST.value)
            return

        email_code = Server.send_verification_code(email, False)
        self.email_code_db_handler.save_email(email)
        self.protocol.send_forgot_password_code_sent(cli_sock)
        response = self.protocol.recv_data(cli_sock)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.FORGOT_PASSWORD_CODE.value:
                client_code = response[1]
                if len(client_code) != 6 or not client_code.isnumeric():
                    self.protocol.send_error(cli_sock, ErrorCodes.INVALID_CODE.value)
                    return

                if self.email_code_db_handler.is_timeout_passed(email):
                    self.email_code_db_handler.delete_email(email)
                    self.protocol.send_error(cli_sock, ErrorCodes.CODE_EXPIRED.value)
                    return

                is_code_correct = (client_code == email_code)
                self.protocol.send_forgot_password_code_status(cli_sock, is_code_correct)
                if not is_code_correct:
                    return

            case ProtocolOpcodes.FORGOT_PASSWORD.value:
                self.handle_forgot_password(cli_sock, addr, response)
                return

            case _:
                self.invalid_request(cli_sock, addr, response)

        response = self.protocol.recv_data(cli_sock)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.RESET_PASSWORD.value:
                new_password = response[1]
                if not Settings.MIN_PASSWORD_LENGTH.value <= len(new_password) <= Settings.MAX_PASSWORD_LENGTH.value:
                    self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
                    return
                if not re.search(r"\d", new_password):
                    self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
                    return
                username = self.db_handler.get_username(email)
                self.db_handler.update_user_password(username, new_password)
                self.email_code_db_handler.delete_email(email)
                logger.info(f"User {username} successfully changed password")
                self.protocol.send_acknowledgment(cli_sock)

            case _:
                self.invalid_request(cli_sock, addr, response)

    def handle_login(self, cli_sock, addr, request: list) -> None:
        current_time = time()
        ip = addr[0]
        # Rate limiting logic
        if ip in self.login_attempts:
            count, last_time = self.login_attempts[ip]
            if current_time - last_time < self.RATE_LIMIT_WINDOW:
                if count >= self.MAX_ATTEMPTS:
                    self.protocol.send_error(cli_sock, ErrorCodes.TOO_MANY_ATTEMPTS.value)
                    logger.warning(f"Rate limit exceeded for {addr}")
                    return
                self.login_attempts[ip] = (count + 1, last_time)
            else:
                self.login_attempts[ip] = (1, current_time)
        else:
            self.login_attempts[ip] = (1, current_time)

        username, password = request[1:]
        if not Settings.MIN_USERNAME_LENGTH.value <= len(username) <= Settings.MAX_USERNAME_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_USERNAME.value)
            logger.warning(f"Invalid username length from {addr}: {username}")
            return
        if not Settings.MIN_PASSWORD_LENGTH.value <= len(password) <= Settings.MAX_PASSWORD_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
            logger.warning(f"Invalid password length from {addr}")
            return
        if not re.search(r"\d", password):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD.value)
            logger.warning(f"Password missing number from {addr}")
            return

        if not self.db_handler.is_username_exist(username) or not self.db_handler.is_password_ok(username, password):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_CREDENTIALS.value)
            logger.warning(f"Failed login attempt for username '{username}' from {addr}")
            return

        self.protocol.send_acknowledgment(cli_sock)
        self.logged_in_users[cli_sock] = username
        logger.info(f"User logged in successfully: {username} from {addr}")

    def handle_logout(self, cli_sock, addr) -> None:
        if cli_sock in self.logged_in_users:
            logger.info(f"User logged out successfully: {self.logged_in_users[cli_sock]}")
            del self.logged_in_users[cli_sock]
            self.protocol.send_acknowledgment(cli_sock)
        else:
            self.protocol.send_error(cli_sock, ErrorCodes.NOT_LOGGED_IN.value)

    def handle_add_domain(self, cli_sock, addr, request: list) -> None:
        if cli_sock not in self.logged_in_users:
            self.protocol.send_error(cli_sock, ErrorCodes.NOT_LOGGED_IN.value)
            return
        username = self.logged_in_users[cli_sock]
        domain = request[1]
        if not DomainsDBHandler.is_valid_domain(domain):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_DOMAIN.value)
            return
        if self.domains_db_handler.is_domain_exist(domain):
            self.protocol.send_error(cli_sock, ErrorCodes.DOMAIN_IN_USE.value)
            return
        self.domains_db_handler.save_domain(domain, username)
        self.protocol.send_acknowledgment(cli_sock)
        logger.info(f"Domain '{domain}' added by user '{username}'")

    def handle_remove_domain(self, cli_sock, addr, request: list) -> None:
        if cli_sock not in self.logged_in_users:
            self.protocol.send_error(cli_sock, ErrorCodes.NOT_LOGGED_IN.value)
            return
        username = self.logged_in_users[cli_sock]
        domain = request[1]
        if not DomainsDBHandler.is_valid_domain(domain, False):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_DOMAIN.value)
            return
        if not self.domains_db_handler.is_domain_exist(domain):
            self.protocol.send_error(cli_sock, ErrorCodes.DOMAIN_NOT_EXIST.value)
            return
        self.domains_db_handler.remove_domain(domain)
        self.protocol.send_acknowledgment(cli_sock)
        logger.info(f"Domain '{domain}' removed by user '{username}'")

    def handle_get_blocked_domains(self, cli_sock) -> None:
        if cli_sock not in self.logged_in_users:
            self.protocol.send_error(cli_sock, ErrorCodes.NOT_LOGGED_IN.value)
            return
        username = self.logged_in_users[cli_sock]
        blocked_domains = self.domains_db_handler.get_user_blocked_domains(username)
        logger.info(f"Blocked domains for user '{username}': {blocked_domains}")
        blocked_domains = [f"{domain},{time_added},{int(still_blocked)}" for domain, time_added, still_blocked in blocked_domains]
        self.protocol.send_blocked_domains_response(cli_sock, blocked_domains)

    def handle_get_all_users(self, cli_sock):
        try:
            if cli_sock not in self.logged_in_users or self.logged_in_users[cli_sock] != Settings.ADMIN_USERNAME.value:
                self.protocol.send_error(cli_sock, ErrorCodes.NOT_ADMIN.value)
                return
            with self.db_handler.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT username, email, password, salt FROM users")
                users = cursor.fetchall()
            # Each user as username,email,password,salt (salt as hex for transport)
            user_strs = [
                f"{username},{email},{password},{salt.hex() if isinstance(salt, bytes) else salt}"
                for username, email, password, salt in users
            ]
            self.protocol.tcp_handler.send_with_size(
                cli_sock,
                f"{ProtocolOpcodes.ALL_USERS_RESPONSE.value}|{'|'.join(user_strs)}",
                key=self.protocol.session_key
            )
        except Exception as e:
            logger.error(f"Error in handle_get_all_users: {e}")
            self.protocol.send_error(cli_sock, ErrorCodes.SERVER_ERROR.value)

    def handle_get_all_domains(self, cli_sock):
        try:
            if cli_sock not in self.logged_in_users or self.logged_in_users[cli_sock] != Settings.ADMIN_USERNAME.value:
                self.protocol.send_error(cli_sock, ErrorCodes.NOT_ADMIN.value)
                return
            domains = self.domains_db_handler.get_all_domains()
            # Each domain as domain,username,time,source,is_blocked
            domain_strs = [
                f"{domain},{username},{time_added},{source if source else ''},{is_blocked}"
                for domain, username, time_added, source, is_blocked in domains
            ]
            self.protocol.tcp_handler.send_with_size(
                cli_sock,
                f"{ProtocolOpcodes.ALL_DOMAINS_RESPONSE.value}|{'|'.join(domain_strs)}",
                key=self.protocol.session_key
            )
        except Exception as e:
            logger.error(f"Error in handle_get_all_domains: {e}")
            self.protocol.send_error(cli_sock, ErrorCodes.SERVER_ERROR.value)

    def handle_delete_user(self, cli_sock, request):
        try:
            if cli_sock not in self.logged_in_users or self.logged_in_users[cli_sock] != Settings.ADMIN_USERNAME.value:
                self.protocol.send_error(cli_sock, ErrorCodes.NOT_ADMIN.value)
                return
            if len(request) < 2:
                self.protocol.send_error(cli_sock, ErrorCodes.INVALID_REQUEST.value)
                return
            username = request[1]
            if username == Settings.ADMIN_USERNAME.value:
                self.protocol.send_error(cli_sock, ErrorCodes.CANNOT_DELETE_ADMIN.value)
                return
            self.db_handler.delete_user(username)
            # Forcibly log out if connected
            to_remove = []
            for sock, uname in self.logged_in_users.items():
                if uname == username:
                    try:
                        self.protocol.send_acknowledgment(sock)
                        sock.close()
                    except Exception:
                        pass
                    to_remove.append(sock)
            for sock in to_remove:
                del self.logged_in_users[sock]
            self.protocol.send_acknowledgment(cli_sock)
            logger.info(f"User '{username}' deleted (and logged out if connected)")
        except Exception as e:
            logger.error(f"Error in handle_delete_user: {e}")
            self.protocol.send_error(cli_sock, ErrorCodes.SERVER_ERROR.value)

    def handle_get_current_username(self, cli_sock):
        username = f"{self.logged_in_users.get(cli_sock, 'guest')}{' (admin)' if cli_sock in self.logged_in_users and self.logged_in_users[cli_sock] == Settings.ADMIN_USERNAME.value else ''}"
        self.protocol.tcp_handler.send_with_size(
            cli_sock,
            f"{ProtocolOpcodes.CURRENT_USERNAME_RESPONSE.value}|{username}",
            key=self.protocol.session_key
        )

    def invalid_request(self, cli_sock, addr, request: list) -> None:
        logger.warning(f"Invalid request received from client at {addr}: {request}")
        self.protocol.send_error(cli_sock, ErrorCodes.INVALID_REQUEST.value)

    def close_client_connection(self, cli_sock, addr):
        logger.info(f"Closing connection with client at {addr}...")
        if cli_sock in self.logged_in_users:
            del self.logged_in_users[cli_sock]
        cli_sock.close()
        self.semaphore.release()

    def run(self):
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(certfile="server.crt", keyfile="server.key")
            self.srv_sock = context.wrap_socket(self.srv_sock, server_side=True)
            self.srv_sock.bind((self.ip, self.port))
            self.srv_sock.listen(Server.BACKLOG)
            logger.info(f"Server listening on {self.ip}:{self.port} with TLS")

            logger.info("Main thread: starting to accept...")
            while True:
                self.email_code_db_handler.clean_expired_codes()
                self.semaphore.acquire()
                cli_sock, addr = self.srv_sock.accept()
                logger.info(f"Main thread: accepted connection from {addr}")
                t: Thread = Thread(
                    target=self.handle_client,
                    args=(cli_sock, addr),
                )
                t.start()
                self.threads.append(t)
        except KeyboardInterrupt:
            logger.info("Main thread: received keyboard interrupt. Shutting down...")
        except error as se:
            logger.error(f"\nMain thread: encountered socket error: {se}")
        except Exception as e:
            logger.error(f"\nMain thread: encountered an unexpected error: {e}")
        finally:
            logger.info("Main thread: waiting for all clients to die")
            for t in self.threads:
                try:
                    t.join()
                except Exception as e:
                    logger.error(f"Error joining thread: {e}")
            self.srv_sock.close()
            self.email_code_db_handler.delete_table()

if __name__ == "__main__":
    if len(argv) == 3:
        ip = argv[1]
        port = int(argv[2])
        s = Server(ip, port)
        s.run()
    else:
        s = Server(IP, PORT)
        s.run()
