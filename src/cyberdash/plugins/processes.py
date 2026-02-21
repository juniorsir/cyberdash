import psutil

class ProcessEngine:
    def get_top_processes(self, limit=8):
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if p.info['name'] and p.info['memory_percent'] is not None:
                    procs.append(p.info)
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        return sorted(procs, key=lambda x: x['memory_percent'], reverse=True)[:limit]
