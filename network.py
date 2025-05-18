import socket, struct
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import logging

__author__ = "Itamar Dalal"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TCPHandler:
    size_header_size = 8

    def __init__(self, debug=False):
        self.TCP_DEBUG = debug
        self.session_key = None  # AES session key for convenience

    def __log(self, prefix, data, max_to_print=100):
        if not self.TCP_DEBUG:
            return
        data_to_log = data[:max_to_print]
        if isinstance(data_to_log, bytes):
            try:
                data_to_log = data_to_log.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        print(f"\n{prefix}({len(data)})>>>{data_to_log}")

    @staticmethod
    def __recv_amount(sock, size=4):
        buffer = b""
        while size:
            new_buffer = sock.recv(size)
            if not new_buffer:
                return b""
            buffer += new_buffer
            size -= len(new_buffer)
        return buffer

    @staticmethod
    def encrypt(message, key):
        cipher = AES.new(key, AES.MODE_CBC)
        ciphertext = cipher.encrypt(pad(message, AES.block_size))
        iv = cipher.iv
        return iv + ciphertext

    @staticmethod
    def decrypt(encrypted_message, key):
        iv = encrypted_message[: AES.block_size]
        ciphertext = encrypted_message[AES.block_size :]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted

    def recv_by_size(self, sock, return_type="string", key=None):
        try:
            data = b""
            size_bytes = self.__recv_amount(sock, self.size_header_size)
            if not size_bytes or size_bytes == b"":
                # Socket closed or no data
                if return_type == "string":
                    return ""
                else:
                    return b""
            try:
                data_len = int(size_bytes)
            except ValueError:
                logger.error(f"Failed to parse data length header: {size_bytes!r}")
                if return_type == "string":
                    return ""
                else:
                    return b""
            if not key:
                data = self.__recv_amount(sock, data_len)
            else:
                data = self.__recv_amount(sock, data_len)
                data = self.decrypt(data, key)
            self.__log("Receive", data)
            if return_type == "string":
                return data.decode()
        except OSError:
            data = "" if return_type == "string" else b""
        return data

    def send_with_size(self, sock, data, key=None):
        if len(data) == 0:
            return
        try:
            if type(data) != bytes:
                data = data.encode()
            original_data = data
            if key:
                data = self.encrypt(data, key)
            len_data = str(len(data)).zfill(self.size_header_size).encode()
            data_to_send = len_data + data
            sock.sendall(data_to_send)
            self.__log("Sent (plaintext)", original_data)
        except OSError:
            if __file__ == "client.py":
                print("Server has disconnected... closing the program")
                exit()

class UDPHandler:
    def __init__(self, debug=False):
        self.UDP_DEBUG = debug

    def __log(self, prefix, data, max_to_print=100):
        if not self.UDP_DEBUG:
            return
        data_to_log = data[:max_to_print]
        if isinstance(data_to_log, bytes):
            try:
                data_to_log = data_to_log.decode()
            except (UnicodeDecodeError, AttributeError):
                pass
        logger.debug(f"{prefix}({len(data)})>>>{data_to_log}")

    def send_to(self, sock, data: bytes, addr):
        """Send data to a specific address using UDP."""
        if len(data) == 0:
            return
        try:
            sock.sendto(data, addr)
            self.__log("Sent", data)
        except OSError as e:
            logger.error(f"Error sending data: {e}")

    def recv_from(self, sock, buffer_size=512):
        """Receive data from a UDP socket."""
        try:
            data, addr = sock.recvfrom(buffer_size)
            self.__log("Received", data)
            return data, addr
        except OSError as e:
            logger.error(f"Error receiving data: {e}")
            return None, None

if __name__ == "__main__":
    pass
