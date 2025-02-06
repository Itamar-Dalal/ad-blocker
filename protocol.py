from enum import Enum
from network import TCPHandler
from socket import socket

class ProtocolOpcodes(Enum):
    ACKNOWLEDGMENT = "ACKG"
    CREATE_USER = "CUSR"
    ERROR = "ERRO"

class Protocol:
    def __init__(self):
        self.tcp_handler = TCPHandler()

    def send_create_account(self, sock: socket, username: str, password: str, email: str) -> None:
        self.tcp_handler.send_with_size(sock, f"{ProtocolOpcodes.CREATE_USER.value}|{username}|{password}|{email}")

    def recv_response(self, sock: socket) -> list:
        response = self.tcp_handler.recv_by_size(sock)
        response = response.split("|")
        if len(response) == 0:
            print("Error in recv_response: invalid response")
            # todo: send error
            raise ValueError("Invalid response")
        return response

if __name__ == "__main__":
    protocol = Protocol()
    #print(protocol.create_account("user", "password", "hi"))