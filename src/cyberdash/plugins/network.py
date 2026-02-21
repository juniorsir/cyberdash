import requests
import socket
import time
import subprocess
import psutil

class NetworkTracker:
    def trace_identity(self):
        """Fetch ISP/IP info with multiple fallbacks."""
        headers = {"User-Agent": "Mozilla/5.0 (Termux; CyberDash)"}
        
        # We try 3 different services in case one is down or rate-limiting you
        endpoints = [
            "https://ipapi.co/json/",      # Priority 1 (Best for ISP names)
            "http://ip-api.com/json/",     # Priority 2 (Very reliable)
            "https://ifconfig.me/all.json" # Priority 3 (Last resort)
        ]
        
        for url in endpoints:
            try:
                res = requests.get(url, headers=headers, timeout=5).json()
                if res and not res.get("error"):
                    # Unify the different API response keys
                    return {
                        "ip": res.get('ip') or res.get('query') or res.get('ip_addr'),
                        "isp": res.get('org') or res.get('isp') or "Unknown ISP",
                        "loc": f"{res.get('city', 'N/A')}, {res.get('country_name') or res.get('country')}"
                    }
            except:
                continue
        return None

    def get_network_state_key(self):
        """Watch local IPs and DNS to detect connection changes."""
        key = ""
        try:
            interfaces = psutil.net_if_addrs()
            for snic in interfaces:
                for addr in interfaces[snic]:
                    key += str(addr.address)
            key += subprocess.getoutput("getprop net.dns1")
            return key
        except:
            return key

    def get_latency(self):
        """Live Latency probe."""
        targets = [("1.1.1.1", 53), ("8.8.8.8", 53), ("google.com", 80)]
        for host, port in targets:
            try:
                start = time.time()
                socket.create_connection((host, port), timeout=2)
                return int((time.time() - start) * 1000)
            except:
                continue
        return -1

    def get_dns_provider(self):
        """DNS leak probe."""
        try:
            trace = requests.get("https://1.1.1.1/cdn-cgi/trace", timeout=2).text
            if "dns=on" in trace: return "Cloudflare (1.1.1.1)"
        except: pass
        try:
            res = requests.get("http://edns.ip-api.com/json", timeout=2).json()
            geo = res.get("dns", {}).get("geo", "")
            if "Cloudflare" in geo: return "Cloudflare DNS"
            if "Google" in geo: return "Google DNS"
            return res.get("dns", {}).get("ip", "ISP Default")
        except:
            return "ISP / Private DNS"
