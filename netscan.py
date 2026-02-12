import socket
import ipaddress
import concurrent.futures
import platform
import subprocess
import sys
from typing import List, Optional

def parse_network(network_input: Optional[str] = None) -> ipaddress.IPv4Network:
    """
    Parse network input or auto-detect local network.
    
    Args:
        network_input: CIDR notation (e.g., '192.168.1.0/24') or None for auto-detect
    
    Returns:
        IPv4Network object
    """
    if network_input:
        try:
            return ipaddress.IPv4Network(network_input, strict=False)
        except ValueError as e:
            raise ValueError(f"Invalid network format: {e}")
    
    # Auto-detect local network
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Create /24 network from local IP
        ip_parts = local_ip.split('.')
        ip_parts[3] = '0'
        network_str = '.'.join(ip_parts) + '/24'
        
        return ipaddress.IPv4Network(network_str, strict=False)
    except Exception as e:
        raise RuntimeError(f"Failed to auto-detect network: {e}")

def ping_host(ip: str, timeout: int = 1) -> bool:
    """
    Ping a single host to check if it's online.
    
    Args:
        ip: IP address to ping
        timeout: Timeout in seconds
    
    Returns:
        True if host is reachable, False otherwise
    """
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    command = ['ping', param, '1', '-w' if platform.system().lower() == 'windows' else '-W', 
               str(timeout * 1000 if platform.system().lower() == 'windows' else timeout), ip]
    
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout + 1
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, Exception):
        return False

def get_hostname(ip: str) -> str:
    """
    Attempt to resolve hostname for an IP address.
    
    Args:
        ip: IP address
    
    Returns:
        Hostname or "Unknown"
    """
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror):
        return "Unknown"

def scan_host(ip: str) -> Optional[dict]:
    """
    Scan a single host and return its information if online.
    
    Args:
        ip: IP address to scan
    
    Returns:
        Dictionary with host info if online, None otherwise
    """
    if ping_host(ip):
        hostname = get_hostname(ip)
        return {
            'ip': ip,
            'hostname': hostname,
            'status': 'online'
        }
    return None

def scan_network(network: ipaddress.IPv4Network, max_workers: int = 50) -> List[dict]:
    """
    Scan all hosts in a network concurrently.
    
    Args:
        network: IPv4Network object to scan
        max_workers: Maximum number of concurrent threads
    
    Returns:
        List of dictionaries containing online host information
    """
    online_hosts = []
    
    print(f"[*] Scanning network: {network}")
    print(f"[*] Total hosts to scan: {network.num_addresses}")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scan tasks
        future_to_ip = {
            executor.submit(scan_host, str(ip)): str(ip) 
            for ip in network.hosts()
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(future_to_ip):
            result = future.result()
            if result:
                online_hosts.append(result)
                print(f"[+] Found: {result['ip']} ({result['hostname']})")
    
    print(f"\n[*] Scan complete. Found {len(online_hosts)} online host(s)")
    return online_hosts

def main():
    """Main entry point for CLI usage."""
    print("=" * 60)
    print(" NetScan - Network Scanner")
    print(" Synerdyn - business@synerdyn.net")
    print("=" * 60 + "\n")
    
    # Get network input
    network_input = sys.argv[1] if len(sys.argv) > 1 else None
    
    try:
        # Parse network
        network = parse_network(network_input)
        
        # Perform scan
        online_hosts = scan_network(network)
        
        # Display results
        if online_hosts:
            print("\nOnline Hosts:")
            print("-" * 60)
            for host in online_hosts:
                print(f"{host['ip']:15} | {host['hostname']}")
        else:
            print("\n[-] No online hosts found")
            
    except Exception as e:
        print(f"[!] Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
