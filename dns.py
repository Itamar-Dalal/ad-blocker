__author__ = "Itamar Dalal"

from socket import socket, AF_INET, SOCK_DGRAM, timeout
import socket as socket_module
from dnslib import DNSRecord
from network import UDPHandler
from database import DomainsDBHandler
import logging
import asyncio
from threading import Thread
from queue import Queue
import time

# Configure logging (DEBUG for troubleshooting, change to WARNING for production)
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

    def __init__(self, listen_ip: str = "0.0.0.0", listen_port: int = DNS_PORT) -> None:
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.blocked_domains = set(DomainsDBHandler().get_domains())  # Only blocked domains
        self.udp_handler = UDPHandler()
        self.sockets = []
        self.active_resolvers = []
        for server in DNSHandler.DNS_RESOLVER_SERVERS:
            try:
                sock = socket(AF_INET, SOCK_DGRAM)
                sock.settimeout(DNSHandler.RESOLVER_TIMEOUT)
                self.sockets.append((sock, server))
                logger.info(f"Created socket for resolver {server}")
            except OSError as e:
                logger.warning(f"Failed to create socket for {server}: {e}")
        if not self.sockets:
            logger.error("No resolver sockets could be created. Exiting.")
            raise RuntimeError("No resolver sockets could be created.")
        self.test_resolvers()  # Initial resolver test
        self.last_resolver_test = time.time()

    def test_resolvers(self) -> None:
        """Test which resolvers are reachable by sending a test query."""
        test_query = DNSRecord.question("example.com").pack()
        response_queue = Queue()

        def query_resolver(sock, server, data, queue):
            try:
                self.udp_handler.send_to(sock, data, server)
                response_data, _ = self.udp_handler.recv_from(sock)
                if response_data:
                    queue.put(server)
                    logger.debug(f"Resolver {server} responded successfully")
            except (timeout, OSError) as e:
                logger.debug(f"Resolver {server} is unreachable: {e}")

        threads = []
        for sock, server in self.sockets:
            t = Thread(target=query_resolver, args=(sock, server, test_query, response_queue))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=self.RESOLVER_TIMEOUT)

        self.active_resolvers = []
        while not response_queue.empty():
            self.active_resolvers.append(response_queue.get())
        
        if not self.active_resolvers:
            logger.warning("No resolvers are reachable. Using all configured resolvers as fallback.")
            self.active_resolvers = [server for _, server in self.sockets]
        logger.info(f"Active resolvers: {self.active_resolvers}")

    def __repr__(self) -> str:
        return f"DNSHandler(listen_ip={self.listen_ip}, listen_port={self.listen_port})"

    def get_cache_key(self, request: DNSRecord) -> tuple:
        """Generate a key for logging purposes (no caching)."""
        domain_name = str(request.q.qname)[:-1]
        return (domain_name, request.q.qtype, request.q.qclass)

    def handle_dns_request(self, data: bytes) -> bytes:
        """Handles incoming DNS requests without caching."""
        try:
            request = DNSRecord.parse(data)
        except Exception as e:
            logger.error(f"Failed to parse DNS request: {e}")
            return b''
        
        key = self.get_cache_key(request)  # Used for logging only
        domain_name = key[0]

        # Periodically retest resolvers
        if time.time() - self.last_resolver_test > self.RESOLVER_TEST_INTERVAL:
            logger.info("Retesting resolvers")
            self.test_resolvers()
            self.last_resolver_test = time.time()

        if self.is_blocked_domain(domain_name):
            logger.info(f"Domain {domain_name} is blocked")
            return self.create_blocked_response(request)
        else:
            logger.info(f"Domain {domain_name} is not blocked, forwarding request")
            dns_response = self.forward_request(data)
            if dns_response:
                return dns_response.pack()
            else:
                logger.warning(f"No response from any DNS resolver for {domain_name}")
                servfail_response = request.reply()
                servfail_response.header.rcode = DNSHandler.SERVFAIL
                return servfail_response.pack()

    def is_blocked_domain(self, domain_name: str) -> bool:
        """Checks if the queried domain is in the blocked list."""
        return domain_name in self.blocked_domains

    def forward_request(self, data: bytes) -> DNSRecord:
        """Forwards the DNS request to the fastest responding resolver."""
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
            t = Thread(target=query_resolver, args=(sock, server, data, response_queue))
            t.start()
            threads.append(t)

        for t in threads:
            t.join(timeout=self.RESOLVER_TIMEOUT)

        return response_queue.get() if not response_queue.empty() else DNSRecord()

    def create_blocked_response(self, request: DNSRecord) -> bytes:
        """Creates a DNS response indicating the domain is blocked."""
        response = request.reply()
        response.header.rcode = DNSHandler.NXDOMAIN
        return response.pack()

    async def handle_client(self, data: bytes, client_addr: tuple, server_sock: socket) -> None:
        """Handles a single DNS request asynchronously."""
        try:
            response = self.handle_dns_request(data)
            if response:
                self.udp_handler.send_to(server_sock, response, client_addr)
                logger.info(f"Sent DNS response to {client_addr}")
            else:
                logger.warning(f"No response generated for request from {client_addr}")
        except Exception as e:
            logger.error(f"Error handling DNS request from {client_addr}: {e}")

    async def handle_socket(self, sock: socket) -> None:
        """Handles incoming requests for a specific socket."""
        loop = asyncio.get_running_loop()
        while True:
            try:
                data, client_addr = await loop.sock_recvfrom(sock, 4096)
                logger.debug(f"Received DNS request from {client_addr}")
                asyncio.create_task(self.handle_client(data, client_addr, sock))
            except Exception as e:
                logger.error(f"Error receiving data on socket: {e}")

    async def run(self) -> None:
        """Runs the DNS server using asyncio for IPv4."""
        try:
            server_sock = socket(AF_INET, SOCK_DGRAM)
            server_sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)
            server_sock.bind((self.listen_ip, self.listen_port))
            server_sock.setblocking(False)
            logger.info(f"DNS server listening on IPv4: {self.listen_ip}:{self.listen_port}")
        except OSError as e:
            logger.error(f"Failed to bind IPv4 socket: {e}")
            return

        await self.handle_socket(server_sock)

    def close(self) -> None:
        """Closes all resolver sockets."""
        for sock, _ in self.sockets:
            try:
                sock.close()
            except Exception as e:
                logger.warning(f"Error closing socket: {e}")

if __name__ == "__main__":
    try:
        dns_handler = DNSHandler()
        asyncio.run(dns_handler.run())
    except KeyboardInterrupt:
        logger.info("Shutting down DNS server")
    except Exception as e:
        logger.error(f"Failed to run DNS server: {e}")
    finally:
        dns_handler.close()