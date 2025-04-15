from socket import socket, AF_INET, SOCK_DGRAM, timeout
from dnslib import DNSRecord, RR, QTYPE, A
from network import TCPHandler
from database import DomainsDBHandler
from cachetools import TTLCache

class DNSHandler:
    DNS_RESOLVER_SERVER = "8.8.8.8"  # Google Public DNS
    DNS_PORT = 53
    RESOLVER_TIMEOUT = 3
    NXDOMAIN = 3  # No such domain
    CACHE_TTL = 300  # Time-to-live for cache entries in seconds
    CACHE_MAX_SIZE = 1000  # Maximum number of entries in the cache

    def __init__(self) -> None:
        self.blocked_domains = DomainsDBHandler().get_domains()
        self.tcp_handler = TCPHandler()
        self.server = (DNSHandler.DNS_RESOLVER_SERVER, DNSHandler.DNS_PORT)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.connect(self.server)
        print(f"Connected to DNS resolver server: {self.server}")
        self.sock.settimeout(DNSHandler.RESOLVER_TIMEOUT)
        self.cache = TTLCache(maxsize=DNSHandler.CACHE_MAX_SIZE, ttl=DNSHandler.CACHE_TTL)

    def __repr__(self) -> str:
        return "DNSHandler()"

    def handle_dns_request(self, data: bytes) -> bytes:
        """Handles incoming DNS requests."""
        request = DNSRecord.parse(data)
        domain_name = str(request.q.qname)[:-1]
        print(f"Received DNS request for: {domain_name}")

        # Check if the domain is in the cache
        if domain_name in self.cache:
            print(f"Cache hit for domain: {domain_name}")
            return self.cache[domain_name]

        if self.is_blocked_domain(domain_name):
            print(f"Domain {domain_name} is blocked.")
            response = self.create_blocked_response(request, domain_name)
        else:
            print(f"Domain {domain_name} is not blocked, forwarding request.")
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
            self.tcp_handler.send_bytes(self.sock, data)
            response_data = self.tcp_handler.recv_by_size(self.sock, return_type="bytes")
            if not response_data:
                return DNSRecord()
            response = DNSRecord.parse(response_data)
            return response
        except timeout:
            print(f"Error: Request to DNS resolver server {self.server} timed out, returning empty response")
            return DNSRecord()
        except Exception as e:
            print(f"Error: {e}")
            return DNSRecord()

    def create_blocked_response(self, query: DNSRecord, domain_name: str) -> bytes:
        """Creates a DNS response indicating the domain is blocked."""
        response = query.reply()
        response.header.rcode = DNSHandler.NXDOMAIN # Set RCODE to NXDOMAIN (3 means No such domain)
        response.add_answer(RR(domain_name, QTYPE.A, rdata=A("0.0.0.0"), ttl=60))
        return response.pack()

def test_dns_handler():
    """Test function for DNSHandler."""
    dns_handler = DNSHandler()

    # Test blocked domain
    blocked_domain = "ads.com"
    query = DNSRecord.question(blocked_domain)
    response = dns_handler.handle_dns_request(query.pack())
    response_record = DNSRecord.parse(response)
    if response_record.header.rcode == 3:
        print("Blocked domain test passed")
    else:
        print("Blocked domain test failed: No response record")

    # Test non-blocked domain
    non_blocked_domain = "example.com"
    query = DNSRecord.question(non_blocked_domain)
    response = dns_handler.handle_dns_request(query.pack())
    response_record = DNSRecord.parse(response)
    if response_record.header.rcode == 0:
        print("Non-blocked domain test passed")
    else:
        print("Non-blocked domain test failed")

    print("All tests completed.")

if __name__ == "__main__":
    test_dns_handler()
