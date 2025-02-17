from sys import argv
from threading import Thread, Semaphore
import socket
from socket import socket, AF_INET, SOCK_STREAM, error
from protocol import Protocol, ProtocolOpcodes, ErrorCodes
from settings import Settings
import re
from random import randrange
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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
                        self.handle_register(cli_sock, request)

                    case _:
                        self.invalid_request(request)
        finally:
            self.close_client_connection(cli_sock, addr)

    def handle_register(self, cli_sock, request: list) -> None:
        username, password, email = request[1:]
        if not Settings.MIN_USERNAME_LENGTH.value <= len(username) <= Settings.MAX_USERNAME_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_USERNAME)
            return
        if not Settings.MIN_PASSWORD_LENGTH.value <= len(password) <= Settings.MAX_PASSWORD_LENGTH.value:
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_PASSWORD)
            return
        # todo: add check for password strength (e.g. at least one uppercase letter, one lowercase letter, one digit, one special character)



        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            self.protocol.send_error(cli_sock, ErrorCodes.INVALID_EMAIL)
            return
        # todo: check if username or email is already in use in the database


        email_code = Server.send_email_verification_code(email)
        self.protocol.send_email_code_sent(cli_sock)
        response = self.protocol.recv_data(cli_sock)
        opcode = response[0]
        match opcode:
            case ProtocolOpcodes.VERIFICATION_CODE.value:
                client_code = response[1]
                if len(client_code) != 6 or not client_code.isnumeric():
                    self.protocol.send_error(cli_sock, ErrorCodes.INVALID_CODE)
                    return
                
                is_code_correct = (client_code == email_code)
                self.protocol.send_verification_code_status(cli_sock, is_code_correct)
                if not is_code_correct:
                    return

            case _:
                self.invalid_request(response)
        
        # todo: add user to the database
        print("User registered successfully: ", username, password, email)
    
    @staticmethod
    def send_email_verification_code(receiver_email: str) -> str:
        code: str = str(randrange(10 ^ Settings.EMAIL_CODE_LENGTH.value, 10 ^ Settings.EMAIL_CODE_LENGTH.value - 1))
        message = MIMEMultipart("alternative")
        message["From"] = Settings.SERVER_EMAIL.value
        message["To"] = receiver_email
        message["Subject"] = "Code for email verification"
        text = f"""\
        Your code for email verification is: {code}
        """
        message.attach(MIMEText(text, "plain"))
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(Settings.SERVER_EMAIL, Settings.SERVER_EMAIL_PASSWORD)
            server.sendmail(Settings.SERVER_EMAIL, receiver_email, message.as_string())
        print(
            f"Email was successfully sent from {Settings.SERVER_EMAIL} to {receiver_email}"
        )
        return code

    def invalid_request(self, cli_sock, addr, request: list) -> None:
        print(f"Invalid request received from client at {addr}: {request}")
        self.protocol.send_error(cli_sock, ErrorCodes.INVALID_REQUEST)

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
