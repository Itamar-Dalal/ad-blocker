import subprocess

class DNSConfig:
    """
    A class to manage DNS server settings for network interfaces on Windows.
    """

    @staticmethod
    def change_dns(interface_name, primary_dns):
        """
        Change DNS server settings for a specified network interface on Windows.
        
        Parameters:
        - interface_name: Name of the network interface (e.g., "Ethernet", "Wi-Fi")
        - primary_dns: Primary DNS server IP address (e.g., "8.8.8.8")
        """
        try:
            # Command to set primary DNS
            cmd = f'netsh interface ip set dns name="{interface_name}" source=static addr={primary_dns}'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                print(f"Error setting primary DNS: {result.stderr}")
                return False
            
            print(f"Primary DNS set to {primary_dns} for {interface_name}")
            return True

        except Exception as e:
            print(f"An error occurred: {e}")
            return False

    @staticmethod
    def get_network_interfaces():
        """
        Retrieve a list of network interface names on the system.
        """
        try:
            cmd = 'netsh interface show interface'
            # Use utf-8 encoding and ignore errors to handle non-ASCII characters
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            
            if result.returncode != 0:
                print(f"Error running netsh command: {result.stderr}")
                return []
            
            interfaces = []
            # Parse the output to extract interface names
            lines = result.stdout.splitlines()
            for line in lines:
                if "Connected" in line and "Name" not in line:
                    parts = line.split()
                    if len(parts) > 3:
                        interface_name = " ".join(parts[3:])
                        interfaces.append(interface_name)
            
            return interfaces
        except Exception as e:
            print(f"Error retrieving interfaces: {e}")
            return []
