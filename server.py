from sys import argv
from threading import Thread, Semaphore
import socket
from socket import socket, AF_INET, SOCK_STREAM, error
from protocol import Protocol, ProtocolOpcodes, ErrorCodes
from settings import Settings
import re
from random import randrange
import smtplib
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from database import DataBaseHandler, EmailCodeDBHandler
from styles import Styles

IP = "0.0.0.0"
PORT = 1234

class Server:
    MAX_CLIENTS = 1000  # Set the maximum number of concurrent clients
    BACKLOG = 5

    def __init__(self, ip=IP, port=PORT) -> None:
        self.ip = ip
        self.port = port
        self.srv_sock = socket(AF_INET, SOCK_STREAM)
        self.srv_sock.bind((self.ip, self.port))
        self.srv_sock.listen(Server.BACKLOG)
        self.threads = []
        self.semaphore = Semaphore(Server.MAX_CLIENTS)
        self.protocol = Protocol()
        self.db_handler = DataBaseHandler()
        self.email_code_db_handler = EmailCodeDBHandler()

    def __repr__(self) -> str:
        return f"Server({self.ip}, {self.port})"
    
    @classmethod
    def create_server(cls) -> "Server":
        """Factory method to create and return a Server instance."""
        return cls()
    
    def handle_client(self, cli_sock, addr):
        try:
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

                    case _:
                        self.invalid_request(cli_sock, addr, request)
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
                    self.protocol.send_error(cli_sock, ErrorCodes.CODE_EXPIRED.value)
                    return

                is_code_correct = (client_code == email_code)
                self.protocol.send_verification_code_status(cli_sock, is_code_correct)
                if not is_code_correct:
                    return
            
            case ProtocolOpcodes.CREATE_USER.value: # user wants to send another email
                self.handle_register(cli_sock, addr, response)
                return

            case _:
                self.invalid_request(cli_sock, addr, response)
                return
        
        self.db_handler.save_user(username, email, password)
        self.email_code_db_handler.delete_email(email)
        print("User registered successfully: ", username, password, email)
    
    @staticmethod
    def send_verification_code(receiver_email: str, to_verify_email: bool) -> str:
        code: str = str(randrange(pow(10, Settings.EMAIL_CODE_LENGTH.value - 1), pow(10, Settings.EMAIL_CODE_LENGTH.value) - 1))
        message = MIMEMultipart("alternative")
        message["From"] = Settings.SERVER_EMAIL.value
        message["To"] = receiver_email
        message["Subject"] = "Email Verification Code - AdBlocker" if to_verify_email else "Forgot Password Code - AdBlocker"
        
        html = f"""\ 
        <html>
        <body>
            <p>Your code for email verification is: <b>{code}</b></p>
            <img src="cid:logo" width="500" height="500">
            <br>
            <i>© 2025 Itamar Dalal</i>
        </body>
        </html>
        """ if to_verify_email else f"""\ 
        <html>
        <body>
            <p>Your code for password reset is: <b>{code}</b></p>
            <img src="cid:logo" width="500" height="500">
            <br>
            <i>© 2025 Itamar Dalal</i>
        </body>
        </html>
        """
        
        message.attach(MIMEText(html, "html"))
        with open(Styles.LOGO_WITH_BACKGROUND_PATH, "rb") as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header("Content-ID", "<logo>")
            message.attach(mime_image)

        with smtplib.SMTP(Settings.SMTP_SERVER.value, Settings.SMTP_PORT.value) as server:
            server.starttls()
            server.login(Settings.SERVER_EMAIL.value, Settings.SERVER_EMAIL_PASSWORD.value)
            server.sendmail(Settings.SERVER_EMAIL.value, receiver_email, message.as_string())
        
        print(
            f"Email was successfully sent from {Settings.SERVER_EMAIL.value} to {receiver_email}"
        )
        return code

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
                    self.protocol.send_error(cli_sock, ErrorCodes.CODE_EXPIRED.value)
                    return

                is_code_correct = (client_code == email_code)
                self.protocol.send_forgot_password_code_status(cli_sock, is_code_correct)
                if not is_code_correct:
                    return
            
            case ProtocolOpcodes.FORGOT_PASSWORD.value: # user wants to send another email
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
                username = self.db_handler.get_username(email)
                self.db_handler.update_user_password(username, new_password)
                self.email_code_db_handler.delete_email(email)
                print("User successfully changed password")
                self.protocol.send_acknowledgment(cli_sock)
            
            case _:
                self.invalid_request(cli_sock, addr, response)    

    def handle_login(self, cli_sock, addr, request: list) -> None:
        username, password = request[1:]
        if not self.db_handler.is_username_exist(username):
            self.protocol.send_error(cli_sock, ErrorCodes.USERNAME_NOT_EXIST.value)
            return
        if not self.db_handler.is_password_ok(username, password):
            self.protocol.send_error(cli_sock, ErrorCodes.INCORRECT_PASSWORD.value)
            return
        self.protocol.send_acknowledgment(cli_sock)
        print("User logged in successfully: ", username, password)        
    
    def invalid_request(self, cli_sock, addr, request: list) -> None:
        print(f"Invalid request received from client at {addr}: {request}")
        self.protocol.send_error(cli_sock, ErrorCodes.INVALID_REQUEST.value)

    def close_client_connection(self, cli_sock, addr):
        print(f"Closing connection with client at {addr}...")
        cli_sock.close()
        self.semaphore.release()
            
    def run(self):
        """Run the server application."""
        try:
            print("Main thread: starting to accept...")
            while True:
                self.semaphore.acquire()
                cli_sock, addr = self.srv_sock.accept()
                print(f"Main thread: accepted connection from {addr}")
                t: Thread = Thread(
                    target=self.handle_client,
                    args=(cli_sock, addr),
                )
                t.start()
                self.threads.append(t)
        except KeyboardInterrupt:
            print("\nMain thread: received keyboard interrupt. Shutting down...")
        except error as se:
            print(f"\nMain thread: encountered socket error: {se}")
        except Exception as e:
            print(f"\nMain thread: encountered an unexpected error: {e}")
        finally:
            print("Main thread: waiting for all clients to die")
            for t in self.threads:
                try:
                    t.join()
                except Exception as e:
                    print(f"Error joining thread: {e}")
            self.srv_sock.close()

if __name__ == "__main__":
    if len(argv) == 3:
        ip = argv[1]
        port = int(argv[2])
        s = Server(ip, port)
        s.run()
    else:
        s = Server(IP, PORT)
        s.run()
