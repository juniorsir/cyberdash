import random
import os
import socket
import asyncio
from collections import deque
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Label, Input, RichLog, Sparkline

# Import Modular Plugins
from plugins.base import ResourceBar
from plugins.hardware import HardwareMonitor
from plugins.network import NetworkTracker
from plugins.processes import ProcessEngine
from plugins.shell import ShellCore

class OverlordApp(App):
    ENABLE_COMMAND_PALETTE = False
    
    # User Bindings
    BINDINGS = [
        ("q", "quit", "Shutdown"),
        ("r", "refresh_net", "Re-trace IP"),
        ("l", "clear_logs", "Wipe Logs"),
        ("h", "help_menu", "Help"),
        ("s", "status_check", "Status"),
    ]

    # Optimized Stealth CSS
    CSS = """
    Screen { background: #000; }
    .panel { border: double #00FF00; background: #050505; padding: 1; }
    
    #top-stats { height: 7; border: round #333; margin: 1; padding: 1; }
    ResourceBar { width: 1fr; margin: 0 2; }
    
    ProgressBar > .bar--bar { color: #00FF00 !important; background: #111; }
    ProgressBar > .bar--complete { color: #00FF00 !important; }
    
    #label { color: #00FF00; margin-bottom: 0; }
    #pct-label { width: 6; margin-left: 1; color: #00FF00; }
    
    #middle-container { height: 1fr; }
    #left-col { width: 40%; }
    #right-col { width: 60%; }
    
    DataTable { height: 1fr; background: #050505; color: #00FF00; border: none; }
    RichLog { background: #000; border: tall #111; }
    
    Input { border: tall #00FF00; color: #00FF00; height: 3; }
    Sparkline { color: #00FF00; height: 3; }
    
    #net-id { height: 7; margin-bottom: 1; color: #00FF00; }
    
    Footer { dock: bottom; height: 1; background: #000; color: #00FF00; margin-top: 1; }
    Footer > .footer--key { color: #FFF; background: #000; }
    Footer > .footer--description { color: #00FF00; background: #000; margin-right: 2; }
    """

    def __init__(self):
        super().__init__()
        # Initialize Logic Plugins
        self.hw = HardwareMonitor()
        self.net = NetworkTracker()
        self.proc = ProcessEngine()
        self.shell = ShellCore()
        
        # UI & Data State
        self.cpu_history = deque([0]*40, maxlen=40)
        self.app_data_cache = None
        self.dns_name = "Detecting..."
        self.last_net_key = self.net.get_network_state_key()
        
        # System Event Templates
        self.HACKER_EVENTS = [
            "[cyan][*][/] Memory clusters optimized.",
            "[green][+][/] Background sync: [bold white]COMPLETE[/]",
            "[red][!][/] Unauthorized ping blocked.",
            "[cyan][*][/] Kernel buffer flushed.",
            "[yellow][!][/] Partition 04: [u]Read-only[/]",
            "[green][+][/] Security protocol: [bold green]ACTIVE[/]",
            "[dim][*] Signal telemetry recalibrated.[/]"
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            # Hardware Status Bar
            with Horizontal(id="top-stats"):
                yield ResourceBar("CPU LOAD", id="cpu-bar")
                yield ResourceBar("RAM USAGE", id="ram-bar")
                yield ResourceBar("STORAGE", id="disk-bar")
            
            # Interactive Core
            with Horizontal(id="middle-container"):
                # Shell & Process Side
                with Vertical(id="left-col", classes="panel"):
                    yield Label("[b][cyan]>_[/] PROCESS ENGINE")
                    yield DataTable(id="proc-table")
                    yield Input(placeholder="Root Shell Access...", id="cmd-input")
                
                # Diagnostics & Log Side
                with Vertical(id="right-col", classes="panel"):
                    yield Label("[b]CPU OSCILLOSCOPE[/]")
                    yield Sparkline(id="cpu-sparkline")
                    
                    yield Label("\n[b]NETWORK IDENTITY[/]")
                    yield Static("[dim]Requesting Satellite Data...[/]", id="net-id")
                    
                    yield Label("\n[b]KERNEL LOGS[/]")
                    yield RichLog(id="sys-log", markup=True)
        yield Footer()

    # --- ACTIONS (Keyboard Shortcuts) ---

    def action_help_menu(self):
        log = self.query_one("#sys-log")
        log.write("\n[bold yellow]=== COMMAND GUIDE ===[/]\n")
        log.write("[white]Q[/]: Shutdown | [white]R[/]: IP Trace | [white]L[/]: Wipe Logs\n")
        log.write("[white]H[/]: Help | [white]S[/]: Diagnostics\n")
        log.write("[dim]Terminal: 'clear' to wipe, 'help' for guide.[/]\n")

    def action_status_check(self):
        log = self.query_one("#sys-log")
        log.write("\n[bold green]>>> INITIATING DIAGNOSTICS...[/]\n")
        uptime = self.shell.execute("uptime -p")
        log.write(f"[cyan][*][/] [white]Uptime:[/] {uptime.strip()}\n")
        log.write(f"[cyan][*][/] [white]DNS Service:[/] {self.dns_name}\n")
        log.write("[bold green]>>> DIAGNOSTICS COMPLETE.[/]\n")

    def action_refresh_net(self):
        self.query_one("#net-id").update("[dim]Re-tracing...[/]")
        self.run_worker(self.fetch_network_info, thread=True)

    def action_clear_logs(self):
        self.query_one("#sys-log").clear()

    # --- CORE WORKERS & UPDATERS ---

    def on_mount(self):
        log = self.query_one("#sys-log")
        self.query_one("#proc-table").add_columns("PID", "NAME", "MEM%")
        
        # Initial Boot UI
        log.write("[yellow][!][/] KERNEL BOOT SEQUENCE INITIATED...\n")
        log.write("[cyan][*][/] MODULE: HardwareMonitor... [green]LOADED[/]\n")
        log.write("[cyan][*][/] MODULE: NetworkTracker... [green]LOADED[/]\n")
        log.write("[white][!][/] SYSTEM OVERLORD [bold green]ONLINE[/].\n")
        
        # Start intervals
        self.set_interval(2.0, self.update_dashboard)
        self.run_worker(self.fetch_network_info, thread=True)

    async def fetch_network_info(self):
        """Fetch heavy network data (IP/ISP/DNS) in background."""
        data = self.net.trace_identity()
        dns = self.net.get_dns_provider()
        if data:
            self.app_data_cache = data
            self.dns_name = dns
            val = f"IP: [y]{data['ip']}[/]\nISP: [y]{data['isp']}[/]\nDNS: [cyan]{dns}[/]"
            self.query_one("#net-id").update(val)

    def update_dashboard(self):
        """Main refresh loop for hardware and live latency."""
        log = self.query_one("#sys-log")
        
        # 1. AUTO-REFRESH NETWORK ON CONNECTIVITY CHANGE
        current_net_key = self.net.get_network_state_key()
        if current_net_key != self.last_net_key:
            self.last_net_key = current_net_key
            log.write("[yellow][!][/] Network change detected. Re-tracing...\n")
            self.run_worker(self.fetch_network_info, thread=True)

        # 2. Hardware Resource Update
        cpu, ram, disk = self.hw.get_stats()
        if cpu == -1.0:
            self.query_one("#cpu-bar").update_bar(0)
            self.query_one("#cpu-bar").query_one("#pct-label").update("[red]LOCK[/]")
            cpu_val = 0
        else:
            self.query_one("#cpu-bar").update_bar(cpu)
            cpu_val = cpu
        
        self.query_one("#ram-bar").update_bar(ram)
        self.query_one("#disk-bar").update_bar(disk)
        
        # Sparkline update
        self.cpu_history.append(cpu_val)
        self.query_one("#cpu-sparkline").data = list(self.cpu_history)
        
        # 3. Network Latency Update (LIVE)
        ms = self.net.get_latency()
        latency_color = "green" if ms < 100 else "yellow" if ms < 300 else "red"
        ms_text = f"[bold {latency_color}]{ms}ms[/]" if ms > 0 else "[red]OFFLINE[/]"
        
        if self.app_data_cache:
            d = self.app_data_cache
            self.query_one("#net-id").update(
                f"IP: [y]{d['ip']}[/]\nISP: [y]{d['isp']}[/]\n"
                f"LOC: [y]{d['loc']}[/]\nDNS: [cyan]{self.dns_name}[/]\n"
                f"LATENCY: {ms_text}"
            )
        elif ms == -1:
             self.query_one("#net-id").update("[red]NO INTERNET CONNECTION[/]")

        # 4. Process Table Update
        table = self.query_one("#proc-table")
        table.clear()
        for p in self.proc.get_top_processes():
            table.add_row(str(p['pid']), p['name'][:12], f"{p['memory_percent']:.1f}%")

        # 5. Background Activity Logs
        if random.random() > 0.8:
            log.write(random.choice(self.HACKER_EVENTS) + "\n")

    async def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        log = self.query_one("#sys-log")
        event.input.value = ""

        if not cmd: return

        if cmd.lower() in ["clear", "cls"]:
            log.clear()
            return
        
        if cmd.lower() == "help":
            self.action_help_menu()
            return

        # NEW: Run the shell command in a background worker
        log.write(f"[bold cyan]#[/] {cmd}\n")
        
        # We define a small internal function to run the command
        def run_shell():
            output = self.shell.execute(cmd)
            # Use call_from_thread to safely update the UI from the worker
            self.call_from_thread(self.post_shell_output, output)

        self.run_worker(run_shell, thread=True)

    def post_shell_output(self, output: str):
        """Callback to print the result once the background task finishes."""
        log = self.query_one("#sys-log")
        if output:
            for line in output.splitlines()[-15:]: # Increased to 15 lines
                log.write(f"  [dim]{line}[/]\n")
        log.scroll_end()

if __name__ == "__main__":
    OverlordApp().run()
