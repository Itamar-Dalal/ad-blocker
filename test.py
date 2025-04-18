import subprocess
import sys
import ctypes

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

def main():
    # Example DNS server (localhost)
    primary_dns = "127.0.0.1"
    
    # Get available network interfaces
    interfaces = get_network_interfaces()
    if not interfaces:
        print("No network interfaces found.")
        sys.exit(1)
    
    print("Available network interfaces:")
    for i, iface in enumerate(interfaces, 1):
        print(f"{i}. {iface}")
    
    # Prompt user to select an interface
    try:
        choice = int(input("Select the interface number to change DNS for: ")) - 1
        if choice < 0 or choice >= len(interfaces):
            print("Invalid selection.")
            sys.exit(1)
        
        interface_name = interfaces[choice]
    except ValueError:
        print("Invalid input. Please enter a number.")
        sys.exit(1)
    
    # Change DNS settings
    if change_dns(interface_name, primary_dns):
        print("DNS settings updated successfully.")
    else:
        print("Failed to update DNS settings.")

if __name__ == "__main__":
    # Check if the script is running with administrative privileges
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("This script must be run as Administrator.")
        sys.exit(1)
    
    main()