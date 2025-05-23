__author__ = "Itamar Dalal"

from socket import socket, AF_INET, SOCK_DGRAM, timeout, SOL_SOCKET, SO_REUSEADDR
from dnslib import DNSRecord
from network import UDPHandler
from database import DomainsDBHandler
from settings import Settings
import logging
import asyncio
from threading import Thread
from queue import Queue
from time import time
import psutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DNSHandler:
    DNS_RESOLVER_SERVERS = [
        ("8.8.8.8", 53), ("1.1.1.1", 53), ("9.9.9.9", 53)
    ]
    DNS_PORT = 53
    RESOLVER_TIMEOUT = 1  # 1 second for compatibility
    NXDOMAIN = 3  # No such domain
    SERVFAIL = 2  # Server failure
    RESOLVER_TEST_INTERVAL = 300  # Retest resolvers every 5 minutes
    CACHE_TTL = 60  # seconds

    def __init__(self, listen_ip: str = "0.0.0.0", listen_port: int = None) -> None:
        """Initialize the DNSHandler with given IP and port, set up resolver sockets."""
        try:
            if listen_port is None:
                listen_port = self.DNS_PORT        
            self.listen_ip = listen_ip
            self.listen_port = listen_port
            self.blocked_domains = set(DomainsDBHandler().get_domains())
            self.udp_handler = UDPHandler()
            self.sockets = []
            self.active_resolvers = []
            self.cache = {}  # (domain, qtype, qclass): (DNSRecord, expire_time)
            self.broadcast_sock = None
            for server in DNSHandler.DNS_RESOLVER_SERVERS:
                try:
                    sock = socket(AF_INET, SOCK_DGRAM)
                    sock.settimeout(DNSHandler.RESOLVER_TIMEOUT)
                    self.sockets.append((sock, server))
                    logger.info(f"Created socket for resolver {server}")
                except OSError as e:
                    logger.error(f"Error creating socket for {server}: {e}")
            if not self.sockets:
                logger.error("No resolver sockets could be created. Exiting.")
            self.test_resolvers()  # Initial resolver test
            self.last_resolver_test = time()
        except Exception as e:
            logger.error(f"Exception in DNSHandler.__init__: {e}")

    def _query_resolver(self, sock, server, data, queue):
        """Send a query to the resolver and put the server in the queue if responsive."""
        try:
            sock.sendto(data, server)
            response, _ = sock.recvfrom(512)
            if response:
                queue.put(server)
        except Exception as e:
            logger.error(f"Exception in _query_resolver for resolver {server}: {e}")

    def test_resolvers(self) -> None:
        """Test which resolvers are reachable by sending a test query."""
        try:
            test_query = DNSRecord.question("example.com").pack()
            response_queue = Queue()
            threads = []
            for sock, server in self.sockets:
                t = Thread(target=self._query_resolver, args=(sock, server, test_query, response_queue))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            self.active_resolvers = []
            while not response_queue.empty():
                try:
                    resolver = response_queue.get_nowait()
                    self.active_resolvers.append(resolver)
                except Exception as ex:
                    logger.error(f"Exception processing response queue: {ex}")
            if not self.active_resolvers:
                logger.warning("No active resolvers found.")
            logger.info(f"Active resolvers: {self.active_resolvers}")
        except Exception as e:
            logger.error(f"Exception in test_resolvers: {e}")

    def __repr__(self) -> str:
        return f"DNSHandler(listen_ip={self.listen_ip}, listen_port={self.listen_port})"

    def get_cache_key(self, request: DNSRecord) -> tuple:
        """Generate a key for caching and logging."""
        try:
            domain_name = str(request.q.qname)[:-1]
            return (domain_name, request.q.qtype, request.q.qclass)
        except Exception as e:
            logger.error(f"Exception in get_cache_key: {e}")
            return ()

    def handle_dns_request(self, data: bytes) -> bytes:
        """Handles incoming DNS requests with caching."""
        try:
            request = DNSRecord.parse(data)
            key = self.get_cache_key(request)
            domain_name = key[0]

            # Periodically retest resolvers
            if time() - self.last_resolver_test > self.RESOLVER_TEST_INTERVAL:
                try:
                    self.test_resolvers()
                except Exception as ie:
                    logger.error(f"Exception retesting resolvers: {ie}")

            # Check cache (only for non-blocked domains)
            if not self.is_blocked_domain(domain_name):
                cached = self.cache.get(key)
                if cached:
                    record, expire_time = cached
                    if time() < expire_time:
                        logger.info(f"Cache hit for {key}")
                        return record.pack()
                    else:
                        logger.info(f"Cache expired for {key}")
                        del self.cache[key]

            if self.is_blocked_domain(domain_name):
                logger.info(f"Domain {domain_name} is blocked")
                return self.create_blocked_response(request)
            else:
                logger.info(f"Domain {domain_name} is not blocked, forwarding request...")
                response = self.forward_request(data)
                if response:
                    # Cache the response
                    self.cache[key] = (response, time() + self.CACHE_TTL)
                    return response.pack()
                else:
                    logger.warning(f"No response from any DNS resolver for {domain_name}")
                    servfail_response = request.reply()
                    servfail_response.header.rcode = DNSHandler.SERVFAIL
                    return servfail_response.pack()
        except Exception as e:
            logger.error(f"Exception in handle_dns_request: {e}")
            return b""

    def is_blocked_domain(self, domain_name: str) -> bool:
        """Checks if the queried domain is in the blocked list."""
        try:
            return domain_name in self.blocked_domains
        except Exception as e:
            logger.error(f"Exception in is_blocked_domain: {e}")
            return False

    def forward_request(self, data: bytes) -> DNSRecord:
        """Forward the DNS request and return a DNS record."""
        try:
            response_queue = Queue()

            def query_resolver(sock, server, data, queue):
                try:
                    self.udp_handler.send_to(sock, data, server)
                    response_data, _ = self.udp_handler.recv_from(sock)
                    if response_data:
                        queue.put(DNSRecord.parse(response_data))
                except timeout:
                    logger.debug(f"Request to {server} timed out")
                except OSError as e:
                    logger.warning(f"Error querying {server}: {e}")

            threads = []
            for sock, server in [(s, srv) for s, srv in self.sockets if srv in self.active_resolvers]:
                try:
                    t = Thread(target=query_resolver, args=(sock, server, data, response_queue))
                    t.start()
                    threads.append(t)
                except Exception as e:
                    logger.error(f"Exception starting thread for resolver {server}: {e}")

            for t in threads:
                try:
                    t.join()
                except Exception as e:
                    logger.error(f"Exception joining thread: {e}")

            return response_queue.get() if not response_queue.empty() else DNSRecord()
        except Exception as e:
            logger.error(f"Exception in forward_request: {e}")
            return DNSRecord()

    def create_blocked_response(self, request: DNSRecord) -> bytes:
        """Create a DNS response for a blocked domain."""
        try:
            response = request.reply()
            response.header.rcode = DNSHandler.NXDOMAIN
            return response.pack()
        except Exception as e:
            logger.error(f"Exception in create_blocked_response: {e}")
            return b""

    async def handle_client(self, data: bytes, client_addr: tuple, server_sock: socket) -> None:
        """Handle an incoming DNS client request asynchronously."""
        try:
            response_data = self.handle_dns_request(data)
            server_sock.sendto(response_data, client_addr)
        except Exception as e:
            logger.error(f"Exception in handle_client: {e}")

    async def handle_socket(self, sock: socket) -> None:
        """Process incoming data from the given socket asynchronously."""
        try:
            loop = asyncio.get_running_loop()
            while True:
                try:
                    data, addr = await loop.sock_recvfrom(sock, 512)
                    asyncio.create_task(self.handle_client(data, addr, sock))
                except Exception as ie:
                    logger.error(f"Exception in handle_socket loop: {ie}")
        except Exception as e:
            logger.error(f"Exception in handle_socket: {e}")

    async def broadcast_listener(self) -> None:
        """Asynchronously listen for LAN broadcast discovery messages."""
        try:
            self.broadcast_sock = socket(AF_INET, SOCK_DGRAM)
            self.broadcast_sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.broadcast_sock.bind(('', Settings.DNS_BROADCAST_PORT.value))
            logger.info(f"Listening for LAN discovery broadcasts on UDP port {Settings.DNS_BROADCAST_PORT.value}")
            loop = asyncio.get_running_loop()
            while True:
                try:
                    data, addr = await loop.sock_recvfrom(self.broadcast_sock, 512)
                    if data.startswith(Settings.DNS_BROADCAST_MESSAGE.value):
                        try:
                            message_parts = data.decode().split("|")
                            if len(message_parts) > 1:
                                interface = message_parts[1]
                                ip_addr = self.get_ip_for_interface(interface)
                                if ip_addr:
                                    logger.info(f"Received LAN discovery from {addr} for interface {interface}, responding with DNS IP")
                                    response = Settings.DNS_BROADCAST_RESPONSE.value + f":{ip_addr}".encode()
                                    await loop.sock_sendto(self.broadcast_sock, response, addr)
                                else:
                                    logger.warning(f"No IP found for interface {interface}")
                            else:
                                logger.warning("Interface not specified in broadcast message")
                        except Exception as e:
                            logger.error(f"Error processing broadcast message: {e}")
                except Exception as e:
                    logger.error(f"Error in broadcast_listener: {e}")
        except Exception as e:
            logger.error(f"Error setting up broadcast listener: {e}")

    @staticmethod
    def get_ip_for_interface(interface_name: str) -> str:
        """Retrieve the IP address for a given network interface."""
        try:
            addrs = psutil.net_if_addrs()
            if interface_name in addrs:
                for snic in addrs[interface_name]:
                    if snic.family.name == 'AF_INET':  # IPv4
                        return snic.address
            logger.warning(f"No IPv4 address found for interface {interface_name}")
            return None
        except Exception as e:
            logger.error(f"Error getting IP for interface {interface_name}: {e}")
            return None

    async def run(self) -> None:
        """Run the DNS server and broadcast listener concurrently."""
        try:
            server_sock = socket(AF_INET, SOCK_DGRAM)
            server_sock.bind((self.listen_ip, self.listen_port))
            logger.info(f"DNS server listening on {self.listen_ip}:{self.listen_port}")

            # Run DNS server and broadcast listener concurrently
            await asyncio.gather(
                self.handle_socket(server_sock),
                self.broadcast_listener()
            )
        except OSError as e:
            logger.error(f"OS error in run: {e}")
        except Exception as e:
            logger.error(f"Exception in DNSHandler.run: {e}")
        finally:
            # Ensure sockets are closed
            self.close()
            if self.broadcast_sock:
                self.broadcast_sock.close()

    def close(self) -> None:
        """Close all sockets used by the DNSHandler."""
        try:
            for sock, _ in self.sockets:
                sock.close()
            if self.broadcast_sock:
                self.broadcast_sock.close()
        except Exception as e:
            logger.error(f"Exception in close: {e}")

    @classmethod
    def create_dns_handler(cls, listen_ip: str = "0.0.0.0", listen_port: int = None) -> "DNSHandler":
        """Create and return a DNSHandler instance with the specified ip and port."""
        try:
            if listen_port is None:
                listen_port = cls.DNS_PORT
            instance = cls(listen_ip, listen_port)
            return instance
        except Exception as e:
            logger.error(f"Exception in DNSHandler.create_handler: {e}")
            return None

if __name__ == "__main__":
    try:
        dns_handler = DNSHandler.create_dns_handler()
        asyncio.run(dns_handler.run())
    except KeyboardInterrupt:
        logger.info("Shutting down DNS server")
    except Exception as e:
        logger.error(f"Failed to run DNS server: {e}")
    finally:
        dns_handler.close()
