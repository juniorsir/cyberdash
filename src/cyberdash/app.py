import random, os, socket, asyncio, subprocess
from collections import deque
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Label, Input, RichLog, Sparkline

# Import Modular Plugins
from .plugins.base import ResourceBar
from .plugins.hardware import HardwareMonitor
from .plugins.network import NetworkTracker
from .plugins.processes import ProcessEngine
from .plugins.shell import ShellCore

class OverlordApp(App):
    ENABLE_COMMAND_PALETTE = True
    
    BINDINGS = [
        ("q", "quit", "Shutdown"),
        ("r", "refresh_net", "Re-trace IP"),
        ("l", "clear_logs", "Wipe Logs"),
        ("h", "help_menu", "Help"),
        ("s", "status_check", "Status"),
        ("k", "kill_process", "Kill Selected"),
    ]

    CSS = """
    Screen { background: #000; opacity: 0%; }
    .panel { border: double #004400; background: #050505; padding: 1; transition: border 500ms; }
    .glow { border: double #00FF00; }
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
    DataTable > .datatable--cursor { background: #00FF00; color: #000; }
    RichLog { background: #000; border: tall #111; }
    Input { border: tall #004400; color: #00FF00; height: 3; transition: border 200ms; }
    Input:focus { border: tall #00FF00; }
    #osc-header { height: 1; margin-bottom: 0; }
    #osc-title { width: 1fr; color: #00FF00; }
    #cpu-temp { width: 12; text-align: right; color: #00FF00; }
    #cpu-sparkline { color: #00FF00; height: 3; min-height: 3; margin-top: 0; }
    #net-id { height: 7; margin-bottom: 1; color: #00FF00; }
    Footer { dock: bottom; height: 1; background: #000; color: #00FF00; margin-top: 1; }
    Footer > .footer--key { color: #FFF; background: #000; text-style: bold; }
    Footer > .footer--description { color: #00FF00; background: #000; margin-right: 2; }
    """

    def __init__(self):
        super().__init__()
        self.hw = HardwareMonitor()
        self.net = NetworkTracker()
        self.proc = ProcessEngine()
        self.shell = ShellCore()
        self.cpu_history = deque([0]*45, maxlen=45)
        self.app_data_cache, self.dns_name = None, "Detecting..."
        self.last_net_key = self.net.get_network_state_key()
        self.HACKER_EVENTS = [
            "[cyan][*][/] Memory optimized.", "[green][+][/] Sync: [b]COMPLETE[/]",
            "[red][!][/] Ping blocked.", "[cyan][*][/] Buffer flushed.",
            "[yellow][!][/] Partition 04: [u]ReadOnly[/]", "[green][+][/] Security: [b]ACTIVE[/]"
        ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            with Horizontal(id="top-stats"):
                yield ResourceBar("CPU LOAD", id="cpu-bar")
                yield ResourceBar("RAM USAGE", id="ram-bar")
                yield ResourceBar("STORAGE", id="disk-bar")
            with Horizontal(id="middle-container"):
                with Vertical(id="left-col", classes="panel"):
                    yield Label("[b][cyan]>_[/] PROCESS ENGINE")
                    yield DataTable(id="proc-table")
                    yield Input(placeholder="Root Shell Access...", id="cmd-input")
                with Vertical(id="right-col", classes="panel"):
                    with Horizontal(id="osc-header"):
                        yield Label("[b]CPU OSCILLOSCOPE[/]", id="osc-title")
                        yield Label("--°C", id="cpu-temp")
                    yield Sparkline(id="cpu-sparkline")
                    yield Label("\n[b]NETWORK IDENTITY[/]")
                    yield Static("[dim]Requesting Satellite Data...[/]", id="net-id")
                    yield Label("\n[b]KERNEL LOGS[/]")
                    yield RichLog(id="sys-log", markup=True)
        yield Footer()

    # --- PROTECTED KILL ACTION ---
    def action_kill_process(self):
        table = self.query_one("#proc-table", DataTable)
        log = self.query_one("#sys-log")
        try:
            row_index = table.cursor_row
            row_data = table.get_row_at(row_index)
            target_pid = int(row_data[0])
            target_name = row_data[1]
            
            # --- SUICIDE PROTECTION ---
            my_pid = os.getpid()
            if target_pid == my_pid:
                log.write("[bold red][!][/] ACCESS DENIED: Suicide protocol blocked.\n")
                return

            # Execute Kill
            self.shell.execute(f"kill -9 {target_pid}")
            log.write(f"[bold red][!][/] SIGKILL SENT TO: {target_name} ({target_pid})\n")
        except:
            log.write("[red][!][/] Selection Error: No target PID found.\n")

    def update_dashboard(self):
        log = self.query_one("#sys-log")
        table = self.query_one("#proc-table")
        current_cursor = table.cursor_row
        
        cpu, ram, disk, is_locked, temp = self.hw.get_stats()
        temp_wid = self.query_one("#cpu-temp")
        if temp:
            t_color = "red" if temp > 70 else "yellow" if temp > 45 else "green"
            temp_wid.update(f"[{t_color}]{temp:.1f}°C[/]")
        else:
            temp_wid.update("[red]N/A[/]")

        if is_locked:
            self.query_one("#cpu-bar").update_bar(0)
            self.query_one("#cpu-bar").query_one("#pct-label").update("[red]LOCK[/]")
            cpu_val = cpu 
        else:
            self.query_one("#cpu-bar").update_bar(cpu)
            cpu_val = cpu
        
        self.query_one("#ram-bar").update_bar(ram)
        self.query_one("#disk-bar").update_bar(disk)
        self.cpu_history.append(cpu_val)
        self.query_one("#cpu-sparkline").data = list(self.cpu_history)
        
        ms = self.net.get_latency()
        ms_text = f"[bold green]{ms}ms[/]" if ms > 0 else "[red]OFFLINE[/]"
        if self.app_data_cache:
            d = self.app_data_cache
            self.query_one("#net-id").update(f"IP: [y]{d['ip']}[/]\nISP: [y]{d['isp']}[/]\nLOC: [y]{d['loc']}[/]\nDNS: [cyan]{self.dns_name}[/]\nLATENCY: {ms_text}")

        table.clear()
        for p in self.proc.get_top_processes():
            table.add_row(str(p['pid']), p['name'][:12], f"{p['memory_percent']:.1f}%")
        
        if current_cursor is not None and current_cursor < len(table.rows):
            table.move_cursor(row=current_cursor)

        if random.random() > 0.8:
            log.write(random.choice(self.HACKER_EVENTS) + "\n")

    async def on_mount(self):
        self.screen.styles.animate("opacity", value=1.0, duration=1.0)
        self.set_interval(1.5, self.pulse_borders)
        table = self.query_one("#proc-table")
        table.add_columns("PID", "NAME", "MEM%")
        table.cursor_type = "row"
        self.set_interval(2.0, self.update_dashboard)
        self.run_worker(self.fetch_network_info, thread=True)

    async def fetch_network_info(self):
        """Fetch heavy network data in background."""
        # This part is slow (Network I/O)
        data = self.net.trace_identity()
        dns = self.net.get_dns_provider()
        
        if data:
            self.app_data_cache = data
            self.dns_name = dns
            
            # FORCE IMMEDIATE UI UPDATE
            ms = self.net.get_latency()
            ms_text = f"[bold green]{ms}ms[/]" if ms > 0 else "[red]OFFLINE[/]"
            
            val = (
                f"IP: [y]{data['ip']}[/]\n"
                f"ISP: [y]{data['isp']}[/]\n"
                f"LOC: [y]{data['loc']}[/]\n"
                f"DNS: [cyan]{dns}[/]\n"
                f"LATENCY: {ms_text}"
            )
            # Update the widget directly from the worker
            self.query_one("#net-id").update(val)
            self.query_one("#sys-log").write("[green][*][/] Identity link established.\n")

    async def on_input_submitted(self, event: Input.Submitted):
        cmd = event.value.strip()
        if not cmd: return
        log = self.query_one("#sys-log")
        event.input.value = ""
        if cmd.lower() in ["clear", "cls"]:
            log.clear()
            return
        log.write(f"[bold cyan]#[/] {cmd}\n")
        self.run_worker(lambda: self.shell_worker(cmd), thread=True)

    def shell_worker(self, cmd):
        output = self.shell.execute(cmd)
        self.call_from_thread(self.display_output, output)

    def display_output(self, output):
        log = self.query_one("#sys-log")
        if output:
            for line in output.splitlines()[-8:]: log.write(f"  [dim]{line}[/]\n")
        log.scroll_end()

    def pulse_borders(self):
        for panel in self.query(".panel"): panel.toggle_class("glow")
    def action_refresh_net(self): self.run_worker(self.fetch_network_info, thread=True)
    def action_clear_logs(self): self.query_one("#sys-log").clear()
    def action_help_menu(self): self.query_one("#sys-log").write("[bold yellow]=== COMMAND GUIDE ===[/]\n")
    def action_status_check(self):
        uptime = self.shell.execute("uptime -p")
        self.query_one("#sys-log").write(f"[cyan][*][/] [white]Uptime:[/] {uptime.strip()}\n")

def run():
    app = OverlordApp()
    app.run()

if __name__ == "__main__":
    run()
