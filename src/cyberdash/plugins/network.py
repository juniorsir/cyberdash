import requests
import socket
import time
import subprocess
import psutil

class NetworkTracker:
    def trace_identity(self):
        """Fetch ISP/IP info."""
        headers = {"User-Agent": "TermuxCyberDash/1.2"}
        try:
            res = requests.get("https://ipapi.co/json/", headers=headers, timeout=5).json()
            if res and not res.get("error"):
                return {
                    "ip": res.get('ip') or res.get('query'),
                    "isp": res.get('org') or res.get('isp'),
                    "loc": f"{res.get('city')}, {res.get('country_name') or res.get('country')}"
                }
        except:
            pass
        return None

    def get_network_state_key(self):
        """
        Creates a fingerprint of the network.
        Now watches local IPs AND System DNS properties.
        """
        key = ""
        try:
            # 1. Watch Local IP changes (Wi-Fi vs Data)
            interfaces = psutil.net_if_addrs()
            for snic in interfaces:
                for addr in interfaces[snic]:
                    key += str(addr.address)
            
            # 2. Watch Android DNS properties
            # If you switch Private DNS, these properties often change
            key += subprocess.getoutput("getprop net.dns1")
            key += subprocess.getoutput("getprop net.dns2")
            
            return key
        except:
            return key

    def get_latency(self):
        """Measure latency (ms)."""
        targets = [("1.1.1.1", 53), ("8.8.8.8", 53), ("google.com", 80)]
        for host, port in targets:
            try:
                start = time.time()
                socket.create_connection((host, port), timeout=2)
                end = time.time()
                return int((end - start) * 1000)
            except:
                continue
        return -1

    def get_dns_provider(self):
        """Identifies the DNS provider handling your traffic."""
        try:
            # Check Cloudflare's diagnostic trace (Very fast)
            trace = requests.get("https://1.1.1.1/cdn-cgi/trace", timeout=2).text
            if "dns=on" in trace: return "Cloudflare (1.1.1.1)"
            if "warp=on" in trace: return "Cloudflare WARP"
        except:
            pass

        try:
            # Server-side DNS leak probe
            res = requests.get("http://edns.ip-api.com/json", timeout=2).json()
            dns_data = res.get("dns", {})
            geo = dns_data.get("geo", "")
            if "Cloudflare" in geo: return "Cloudflare DNS"
            if "Google" in geo: return "Google DNS"
            if "OpenDNS" in geo: return "OpenDNS"
            
            ip = dns_data.get("ip", "")
            return f"Resolver ({ip[:15]})" if ip else "ISP Default"
        except:
            return "ISP / Private DNS"
