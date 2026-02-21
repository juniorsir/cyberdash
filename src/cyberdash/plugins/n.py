import requests

class NetworkTracker:
    def trace_identity(self):
        headers = {"User-Agent": "TermuxCyberDash/1.2"}
        # List of URLs to try
        urls = ["https://ipapi.co/json/", "http://ip-api.com/json/"]
        
        for url in urls:
            try:
                # Short 3-second timeout to prevent UI hanging
                res = requests.get(url, headers=headers, timeout=3).json()
                if res:
                    return {
                        "ip": res.get('ip') or res.get('query'),
                        "isp": res.get('org') or res.get('isp'),
                        "loc": f"{res.get('city')}, {res.get('country_name') or res.get('country')}"
                    }
            except:
                continue
        return None
   
    def get_latency(self):
        """Measure latency (ms) to Cloudflare DNS."""
        target = "1.1.1.1"
        try:
            start = time.time()
            # Try a TCP connection to port 53 (DNS)
            socket.create_connection((target, 53), timeout=2)
            end = time.time()
            return int((end - start) * 1000)
        except:
            return -1

    def get_dns_provider(self):
        """Identify current DNS provider."""
        try:
            # On Termux/Android, we check getprop
            dns_ip = subprocess.getoutput("getprop net.dns1").strip()
            if not dns_ip:
                # Fallback for standard Linux
                with open("/etc/resolv.conf", "r") as f:
                    for line in f:
                        if line.startswith("nameserver"):
                            dns_ip = line.split()[1]
                            break
            
            # Map common IPs to names
            mapping = {
                "1.1.1.1": "Cloudflare",
                "1.0.0.1": "Cloudflare",
                "8.8.8.8": "Google Public DNS",
                "8.8.4.4": "Google Public DNS",
                "9.9.9.9": "Quad9",
                "208.67.222.222": "OpenDNS"
            }
            return mapping.get(dns_ip, dns_ip if dns_ip else "System Default")
        except:
            return "Internal/Protected"
