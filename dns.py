__author__ = "Itamar Dalal"

from socket import socket, AF_INET, SOCK_DGRAM, timeout
import socket as socket_module
from dnslib import DNSRecord, RR, QTYPE, A
from network import UDPHandler
from database import DomainsDBHandler
from cachetools import TTLCache
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DNSHandler:
    DNS_RESOLVER_SERVER = "8.8.8.8"  # Google Public DNS
    DNS_PORT = 53
    RESOLVER_TIMEOUT = 3
    NXDOMAIN = 3  # No such domain
    CACHE_TTL = 300  # Cache TTL in seconds
    CACHE_MAX_SIZE = 1000

    def __init__(self, listen_ip: str = "0.0.0.0", listen_port: int = DNS_PORT) -> None:
        self.listen_ip = listen_ip
        self.listen_port = listen_port
        self.blocked_domains = DomainsDBHandler().get_domains()
        self.udp_handler = UDPHandler()
        self.server = (DNSHandler.DNS_RESOLVER_SERVER, DNSHandler.DNS_PORT)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.connect(self.server)
        logger.info(f"Connected to DNS resolver server: {self.server}")
        self.sock.settimeout(DNSHandler.RESOLVER_TIMEOUT)
        self.cache = TTLCache(maxsize=DNSHandler.CACHE_MAX_SIZE, ttl=DNSHandler.CACHE_TTL)

    def __repr__(self) -> str:
        return f"DNSHandler(listen_ip={self.listen_ip}, listen_port={self.listen_port})"

    def handle_dns_request(self, data: bytes) -> bytes:
        """Handles incoming DNS requests."""
        request = DNSRecord.parse(data)
        domain_name = str(request.q.qname)[:-1]
        logger.info(f"Received DNS request for: {domain_name}")

        if domain_name in self.cache:
            logger.info(f"Cache hit for domain: {domain_name}")
            return self.cache[domain_name]

        if self.is_blocked_domain(domain_name):
            logger.info(f"Domain {domain_name} is blocked")
            response = self.create_blocked_response(request, domain_name)
        else:
            logger.info(f"Domain {domain_name} is not blocked, forwarding request")
            response = self.forward_request(data).pack()

        # Store the response in the cache
        self.cache[domain_name] = response
        return response

    def is_blocked_domain(self, domain_name: str) -> bool:
        """Checks if the queried domain is in the blocked list."""
        return domain_name in self.blocked_domains

    def forward_request(self, data: bytes) -> DNSRecord:
        """Forwards the DNS request to an external resolver and retrieves the response."""
        try:
            self.udp_handler.send_to(self.sock, data, self.server)
            response_data, _ = self.udp_handler.recv_from(self.sock)
            if not response_data:
                logger.warning("Received empty response from DNS resolver")
                return DNSRecord()
            return DNSRecord.parse(response_data)
        except timeout:
            logger.error(f"Request to DNS resolver server {self.server} timed out")
            return DNSRecord()
        except Exception as e:
            logger.error(f"Error forwarding DNS request: {e}")
            return DNSRecord()

    def create_blocked_response(self, query: DNSRecord, domain_name: str) -> bytes:
        """Creates a DNS response indicating the domain is blocked."""
        response = query.reply()
        response.header.rcode = DNSHandler.NXDOMAIN  # Set RCODE to NXDOMAIN (3 means No such domain)
        response.add_answer(RR(domain_name, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
        return response.pack()

    def run(self) -> None:
        """Runs the DNS server to handle incoming DNS requests."""
        with socket(AF_INET, SOCK_DGRAM) as server_sock:
            server_sock.setsockopt(socket_module.SOL_SOCKET, socket_module.SO_REUSEADDR, 1)  # Allow address reuse
            server_sock.bind((self.listen_ip, self.listen_port))
            logger.info(f"DNS server running on {self.listen_ip}:{self.listen_port}")
            while True:
                try:
                    data, client_addr = self.udp_handler.recv_from(server_sock)
                    if data is None:
                        continue
                    logger.info(f"Received DNS request from {client_addr}")
                    response = self.handle_dns_request(data)
                    self.udp_handler.send_to(server_sock, response, client_addr)
                    logger.info(f"Sent DNS response to {client_addr}")
                except Exception as e:
                    logger.error(f"Error handling DNS request: {e}")

if __name__ == "__main__":
    dns_handler = DNSHandler()
    dns_handler.run()
