from PyQt6.QtWidgets import QApplication
import gui
from socket import socket, AF_INET, SOCK_STREAM
from typing import Callable
import re

class Client:
    def __init__(self) -> None:
        """Initialize the Client class."""
        self.app = QApplication([])
        self.window = None
        self.server = None

    def __repr__(self) -> str:
        """Return a string representation of the Client."""
        return f"Client()"
    
    @classmethod
    def create_client(cls) -> "Client":
        """Factory method to create and return a Client instance."""
        return cls()
    
    def verify_args(call: Callable):
        def func(self, ip: str, port: str):
            if ip == "" or port == "":
                self.window.connect_to_server_window(
                    f"IP and Port cannot be empty."
                )
                return
            
            # Regular expression to validate IPv4 addresses
            ip_regex = r"^(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\." \
                       r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\." \
                       r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)\." \
                       r"(25[0-5]|2[0-4][0-9]|[0-1]?[0-9][0-9]?)$"

            # Validate IP
            if not re.match(ip_regex, ip):
                self.window.connect_to_server_window(
                    f"Invalid IP: {ip}. IP must be in the format [0-255].[0-255].[0-255].[0-255]."
                )
                return
            # Validate Port
            if not port.isnumeric() or not (1 <= int(port) <= 65535):
                self.window.connect_to_server_window(
                    f"Invalid port: {port}. Port must be a number between 1 and 65535."
                )
                return

            return call(self, ip, port)

        return func


    @verify_args 
    def connect_to_server(self, ip: str, port: str) -> None:
        try:
            self.server = socket(AF_INET, SOCK_STREAM)
            self.server.connect((ip, int(port)))
        except ConnectionRefusedError:
            self.window.connect_to_server_window(
                f"Cannot find the server. Please enter a different IP or port."
            )

    def run(self):
        self.window = gui.MainWindow(self)
        self.window.show()
        self.app.exec()


if __name__ == "__main__":
    c = Client.create_client()
    c.run()
