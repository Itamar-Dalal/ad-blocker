from socket import socket, AF_INET, SOCK_DGRAM, timeout
from dnslib import DNSRecord, RR, QTYPE, A
from tcp_by_size import TCPHandler

class DNSHandler:
    DNS_RESOLVER_SERVER = "8.8.8.8"  # Google Public DNS
    DNS_PORT = 53
    RESOLVER_TIMEOUT = 3

    def __init__(self) -> None:
        self.blocked_domains = ["ads.example.com", "ads.com"]
        self.tcp_handler = TCPHandler()

        self.server = (DNSHandler.DNS_RESOLVER_SERVER, DNSHandler.DNS_PORT)
        self.sock = socket(AF_INET, SOCK_DGRAM)
        self.sock.connect(self.server)
        print(f"Connected to DNS resolver server: {self.server}")
        self.sock.settimeout(DNSHandler.RESOLVER_TIMEOUT)

    def __repr__(self) -> str:
        return "DNSHandler()"

    def handle_dns_request(self, data: bytes) -> bytes:
        """Handles incoming DNS requests."""
        request = DNSRecord.parse(data)
        domain_name = str(request.q.qname)[:-1]
        print(f"Received DNS request for: {domain_name}")

        if self.is_blocked_domain(domain_name):
            print(f"Domain {domain_name} is blocked.")
            return self.create_blocked_response(request, domain_name)
        else:
            print(f"Domain {domain_name} is not blocked, forwarding request.")
            response = self.forward_request(data)
            return response.pack()

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
            print(f"Error: Request to DNS resolver server {self.server} timed out, returning empty response.")
            return DNSRecord()
        except Exception as e:
            print(f"Error: {e}")
            return DNSRecord()

    def create_blocked_response(self, query: DNSRecord, domain_name: str) -> bytes:
        """Creates a DNS response indicating the domain is blocked."""
        response = query.reply()
        response.header.rcode = 3  # Set RCODE to NXDOMAIN (3 means No such domain)
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
