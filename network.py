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

    def send_bytes(self, sock, data: bytes) -> None:
        if len(data) == 0:
            return
        try:
            sock.sendall(data)
            self.__log("Sent Bytes", data.hex())
        except OSError as e:
            print(f"Error sending bytes: {e}")

    @staticmethod
    def __hex(s):
        cnt = 0
        for i in range(len(s)):
            if cnt % 16 == 0:
                print("")
            elif cnt % 8 == 0:
                print("    ", end="")
            cnt += 1
            print("%02X" % int(ord(s[i])), end="")

    def send_one_message(self, sock, data):
        try:
            length = socket.htonl(len(data))
            if type(data) != bytes:
                data = data.encode()
            sock.sendall(struct.pack("I", length) + data)
            data_part = data[:100]
            if self.TCP_DEBUG and len(data) > 0:
                print(f"\nSent({len(data)})>>>{data_part}")
        except:
            print(f"ERROR in send_one_message")

    def recv_one_message(self, sock, return_type="string"):
        len_section = self.__recv_amount(sock, 4)
        if not len_section:
            return None
        (len_int,) = struct.unpack("I", len_section)
        len_int = socket.ntohl(len_int)
        data = self.__recv_amount(sock, len_int)
        if self.TCP_DEBUG and len(data) != 0:
            print(f"\nRecv({len_int})>>>{data[:100]}")

        if len_int != len(data):
            data = b""
        if return_type == "string":
            return data.decode()

        return data

    def main_for_test(self, role):
        import socket
        import time

        port = 12312
        if role == "srv":
            s = socket.socket()
            s.bind(("0.0.0.0", port))
            s.listen(1)
            cli_s, addr = s.accept()
            data = self.recv_by_size(cli_s)
            print("1 server got:" + data)
            self.send_with_size(cli_s, "1 back:" + data)
            time.sleep(3)

            print("\n\n\nServer Binary Section\n")
            data = self.recv_one_message(cli_s)
            print("2 server got:" + data)
            self.send_one_message(cli_s, "2 back:" + data)

            cli_s.close()
            time.sleep(3)
            s.close()
        elif role == "cli":
            c = socket.socket()
            c.connect(("127.0.0.1", port))
            self.send_with_size(c, "ABC")

            print("1 client got:" + self.recv_by_size(c))
            time.sleep(3)

            print("\n\n\nClient Binary Section\n")
            self.send_one_message(c, "abcdefghijklmnop")

            print("2 client got:" + self.recv_one_message(c))
            time.sleep(3)
            c.close()

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
    import sys

    handler = TCPHandler()
    if len(sys.argv) >= 2:
        handler.main_for_test(sys.argv[1])
