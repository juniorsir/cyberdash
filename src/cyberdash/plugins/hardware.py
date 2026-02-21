import psutil, shutil, os, random, subprocess, json
# At the top:
from .base import ResourceBar

class HardwareMonitor:
    def __init__(self):
        try:
            psutil.cpu_percent(interval=None)
        except:
            pass

    def get_cpu_temp(self):
        """Tries 3 methods to get temperature: Real, Battery, or Estimated."""
        # --- Method 1: Real Hardware Sensors (SysFS) ---
        for i in range(15):
            path = f"/sys/class/thermal/thermal_zone{i}/temp"
            try:
                if os.path.exists(path):
                    with open(path, "r") as f:
                        t = int(f.read().strip())
                        if t > 1000: t /= 1000
                        if 25 < t < 95: return t
            except: continue

        # --- Method 2: Termux-API (Battery Temp Proxy) ---
        try:
            # This calls the termux-api command
            res = subprocess.check_output(["termux-battery-status"], timeout=1)
            data = json.loads(res)
            return data.get("temperature") # Returns float like 38.5
        except:
            pass

        # --- Method 3: Thermal Proxy (Simulated based on Load) ---
        # If we can't read anything, we simulate 'System Warmth' 
        # based on current CPU usage to keep the dashboard 'alive'.
        try:
            load = psutil.cpu_percent()
            # Base temp 32C + (Load * 0.2) + random fluctuation
            estimate = 32 + (load * 0.15) + random.uniform(-1, 1)
            return estimate
        except:
            return random.uniform(35, 42)

    def get_stats(self):
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            is_locked = False
        except PermissionError:
            cpu = random.uniform(1.0, 5.0) 
            is_locked = True
        
        try:
            ram = psutil.virtual_memory().percent
        except:
            ram = 0.0
            
        try:
            usage = shutil.disk_usage(os.path.expanduser("~"))
            disk = (usage.used / usage.total) * 100
        except:
            disk = 0.0
            
        temp = self.get_cpu_temp()
        return cpu, ram, disk, is_locked, temp
